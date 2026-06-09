# Prática 11 — Kubernetes local com Kind (Aula 6)

> **Objetivo:** subir a CloudTask em um **cluster Kubernetes local** usando
> [**Kind**](https://kind.sigs.k8s.io/) (Kubernetes IN Docker). Você verá:
> - cluster de 1 nó criado em containers Docker;
> - Postgres + API empacotados em **Deployments**, expostos via **Services**;
> - configuração separada em **ConfigMap** (visível) e **Secret** (sensível);
> - rolling update funcionando ao mexer no manifest;
> - a mesma lição da Semana 2 sobre **perda de dados** (Postgres como Pod sem
>   volume persistente).
>
> **Quando:** Semana 3 / Aula 6.
> **Tempo:** 30–45 min (primeira vez).
> **Custo:** $0 (tudo local).
>
> **Pré-req:**
> - Devcontainer da semana-03 rodando.
> - **Docker Desktop** ligado no HOST.
> - **Kind** instalado **no HOST** (Windows/macOS/Linux).
> - **`kubectl`** disponível (já vem no devcontainer; instale no host também
>   para os comandos `kind` ficarem práticos).
> - Conceito de base: [`../conceitos/infra-aws-minima-por-semana.md`](../conceitos/infra-aws-minima-por-semana.md) (seção EKS).

---

## 0. Por que Kind, e por que rodar no HOST

`kind` cria um cluster Kubernetes onde **cada nó é um container Docker**.
Ele precisa do **daemon Docker do host** para criar esses containers e
expor portas para `localhost`.

> ⚠️ **Os comandos `kind create / delete / load` rodam no terminal DO HOST**
> (Windows PowerShell, macOS Terminal, Linux shell). Não dentro do
> devcontainer. Já o **`kubectl`** funciona em ambos — dentro do
> devcontainer ele lê `~/.kube/config` montado do host e fala com o
> cluster pelo IP exposto pelo Kind.

### Instalar Kind no host (uma vez)

| SO | Comando |
| --- | --- |
| Windows (Chocolatey) | `choco install kind` |
| Windows (winget) | `winget install Kubernetes.kind` |
| macOS (brew) | `brew install kind` |
| Linux | `curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && chmod +x kind && sudo mv kind /usr/local/bin/` |

Verificar:

```bash
kind version
# kind v0.23.0+ ...
```

---

## 1. Conhecer os manifests

Os manifests vivem em `infra/k8s/`. Leia os comentários — cada arquivo
explica **por que** cada decisão foi tomada.

```text
infra/k8s/
├── README.md                   ← índice rápido
├── kind-config.yaml            ← cluster Kind (1 nó, porta 30080 → host)
├── namespace.yaml              ← namespace cloudtask
├── configmap.yaml              ← configs não sensíveis
├── secret.example.yaml         ← TEMPLATE — copie para secret.yaml
├── postgres-deployment.yaml    ← Postgres como Pod (sem volume! didático)
├── postgres-service.yaml       ← DNS interno postgres:5432
├── api-deployment.yaml         ← API FastAPI 2 réplicas + probes
├── api-service.yaml            ← NodePort 30080
└── kustomization.yaml          ← apply de tudo em ordem
```

---

## 2. Criar o cluster Kind (no HOST)

> Comandos abaixo: **terminal do host**.

```bash
# Estando na raiz do repo:
kind create cluster --config infra/k8s/kind-config.yaml
```

Saída esperada (~1–2 min):

```text
Creating cluster "cloudtask" ...
 ✓ Ensuring node image (kindest/node:v1.30.0)
 ✓ Preparing nodes
 ✓ Writing configuration
 ✓ Starting control-plane
 ✓ Installing CNI
 ✓ Installing StorageClass
Set kubectl context to "kind-cloudtask"
You can now use your cluster with:
  kubectl cluster-info --context kind-cloudtask
```

Confirmar:

```bash
kubectl cluster-info
kubectl get nodes
# cloudtask-control-plane   Ready   control-plane   1m
```

---

## 3. Carregar a imagem da API no Kind

Kind não puxa de Docker Hub automaticamente para imagens que **não existem
ali**. Como `cloudtask-api:prod` é uma imagem local, precisamos **importar
no cluster**:

```bash
# Build (no HOST — usa o mesmo Docker daemon do Kind)
docker build --target prod -t cloudtask-api:prod .

# Load no cluster Kind
kind load docker-image cloudtask-api:prod --name cloudtask
```

> 💡 **Sem este `kind load`**, o Pod ficaria em `ErrImagePull` tentando
> baixar `cloudtask-api:prod` do Docker Hub (onde não existe).

> ⚠️ **Por que `prod` e não `dev`?** O target `dev` do Dockerfile **não
> embute o código** (`app/`): ele espera o código montado por **volume**,
> coisa que o devcontainer faz mas o cluster Kind **não**. Rodar a imagem
> `dev` no cluster derruba o Pod em **`CrashLoopBackOff`** com
> `ModuleNotFoundError: No module named 'app'`, porque o `uvicorn
> app.main:app` não encontra o pacote. O target `prod` faz
> `COPY app/ /app/app/` — imagem autossuficiente, que é o que um cluster
> precisa. (Custo: sem `--reload`/hot-reload — mas no cluster o código é
> imutável de qualquer forma.)

---

## 4. Criar o Secret real (a partir do template)

```bash
cp infra/k8s/secret.example.yaml infra/k8s/secret.yaml
```

Gere valores reais e atualize `secret.yaml`:

```bash
# DENTRO DO DEVCONTAINER (terminal do VS Code)
PG_PASS="$(openssl rand -hex 16)"
SECRET_KEY="$(openssl rand -hex 32)"

echo "POSTGRES_USER=$(echo -n 'cloudtask' | base64)"
echo "POSTGRES_PASSWORD=$(echo -n "$PG_PASS" | base64)"
echo "SECRET_KEY=$(echo -n "$SECRET_KEY" | base64)"
echo "DATABASE_URL=$(echo -n "postgresql://cloudtask:$PG_PASS@postgres:5432/cloudtask" | base64)"
```

Cole os valores nos campos `data:` de `secret.yaml` e **adicione a entrada
de `secret.yaml` no `kustomization.yaml`** (descomente a linha).

> ⚠️ `secret.yaml` já está coberto pelo `.gitignore`. Nunca commite.

---

## 5. Aplicar tudo (do devcontainer ou do host — tanto faz)

```bash
kubectl apply -k infra/k8s/

# Acompanhar
kubectl get pods -n cloudtask -w
```

Esperado (~30 s):

```text
NAME                        READY   STATUS              RESTARTS   AGE
postgres-xxxxxxx-yyyyy      0/1     ContainerCreating   0          5s
postgres-xxxxxxx-yyyyy      1/1     Running             0          15s
api-xxxxxxx-yyyyy           0/1     Init:0/1            0          5s
api-xxxxxxx-yyyyy           0/1     Running             0          20s
api-xxxxxxx-yyyyy           1/1     Running             0          25s
api-xxxxxxx-zzzzz           1/1     Running             0          25s
```

> 💡 O Pod da API fica em `Init:0/1` enquanto o `initContainer wait-for-postgres`
> espera o Postgres ficar pronto.

`Ctrl+C` para sair do watch.

---

## 6. Testar a API

```bash
# Health
curl http://localhost:30080/health
# {"status":"ok"}

# Ready (consulta o Postgres)
curl http://localhost:30080/health/ready
# {"status":"ok","database":"ok"}

# Criar tarefa
curl -X POST http://localhost:30080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Tarefa no K8s","priority":"high"}'

# Listar
curl http://localhost:30080/tasks

# Swagger
echo "Abra http://localhost:30080/docs"
```

---

## 7. Ver o Service balanceando entre os 2 Pods

A API roda em **2 réplicas** (2 Pods). O `Service` distribui as requisições
entre eles. Mas como **ver** isso acontecer?

> ❌ **Não dá para usar o `/health` para isso.** O endpoint `/health` da
> CloudTask **não devolve o nome do Pod** que respondeu — então um loop que
> chama `/health` não consegue dizer qual Pod atendeu.

A forma que **funciona**: olhar os **logs dos 2 Pods ao mesmo tempo** num
terminal e **disparar requisições** noutro. Cada requisição vira uma linha
de log no Pod que a atendeu — com `--prefix`, o `kubectl` carimba o **nome
do Pod** em cada linha. Você vê as linhas alternando entre os dois Pods.

### Precisa de DOIS terminais (PowerShell)

> Os dois podem ser abas/janelas do **PowerShell no host** (ou no
> devcontainer — `kubectl` funciona nos dois). Abra os dois **antes** de
> começar.

**Terminal 1 — seguir os logs dos 2 Pods (deixe rodando):**

```powershell
# --prefix  -> carimba [pod/api-xxxx/api] em cada linha (mostra QUAL Pod)
# --tail=0  -> ignora o histórico; só mostra linhas NOVAS a partir de agora
# -f        -> "follow": fica preso seguindo (não retorna sozinho)
kubectl logs -n cloudtask -l app=api -f --prefix --tail=0
```

Esse comando **trava** seguindo os logs — é o comportamento esperado.
Deixe-o aberto.

**Terminal 2 — disparar 20 requisições, uma por vez:**

```powershell
foreach ($i in 1..20) {
  curl.exe -s http://localhost:30080/tasks | Out-Null
  Start-Sleep -Milliseconds 200
}
```

> 💡 `curl.exe` (com `.exe`) e **não** `curl` — no PowerShell, `curl` é
> apelido de `Invoke-WebRequest`, que tem outra sintaxe. O `.exe` força o
> curl de verdade. `Out-Null` joga fora o corpo da resposta (só queremos
> gerar tráfego).

### O que observar

No **Terminal 1**, conforme o Terminal 2 dispara, aparecem linhas de
`GET /tasks` **com prefixos de Pod diferentes alternando**, por exemplo:

```text
[pod/api-774964db5f-k2q24/api] INFO:  10.244.0.1:0 - "GET /tasks HTTP/1.1" 200 OK
[pod/api-774964db5f-l4mhc/api] INFO:  10.244.0.1:0 - "GET /tasks HTTP/1.1" 200 OK
[pod/api-774964db5f-k2q24/api] INFO:  10.244.0.1:0 - "GET /tasks HTTP/1.1" 200 OK
[pod/api-774964db5f-l4mhc/api] INFO:  10.244.0.1:0 - "GET /tasks HTTP/1.1" 200 OK
```

Dois nomes de Pod (`...k2q24` e `...l4mhc`) se revezando = **o Service está
balanceando**. `Ctrl+C` no Terminal 1 para sair.

> ⚠️ **Não viu alternar?** O `Service`/`kube-proxy` balanceia **por
> conexão**. Cada `curl.exe` abre uma conexão nova, então deveria revezar —
> mas a distribuição é aleatória, não um-a-um perfeito. Dispare **mais**
> requisições (suba o `1..20` para `1..50`) e você verá os dois Pods
> aparecerem. Se **só um** Pod aparecer sempre, confira que há 2 Pods
> `Running`: `kubectl get pods -n cloudtask`.

---

## 8. Rolling update — mudar uma config e ver o redeploy

Edite `infra/k8s/configmap.yaml` mudando `LOG_LEVEL: "INFO"` para `"DEBUG"`.

```bash
kubectl apply -k infra/k8s/

# Força o rollout (ConfigMap mudou, mas Pods não reiniciam automaticamente)
kubectl rollout restart deployment/api -n cloudtask

# Acompanhar
kubectl rollout status deployment/api -n cloudtask
```

Você verá novos Pods subindo **enquanto os antigos ainda servem**
(maxUnavailable: 0). Zero downtime.

---

## 9. **A demonstração dolorosa:** perda de dados (de novo)

> **Por que repetir a demo que já fizemos no Fargate?** Para o aluno
> internalizar: **independente de Fargate, Kind, EKS — Postgres em
> container sem volume persistente sempre perde dados**.

```bash
# 1. Listar tarefas atuais
curl -s http://localhost:30080/tasks | jq 'length'
# (>= 1, do passo 6)

# 2. Forçar deleção do Pod do Postgres
kubectl delete pod -n cloudtask -l app=postgres

# 3. Aguardar o Deployment recriar
kubectl wait -n cloudtask --for=condition=ready pod -l app=postgres --timeout=60s

# 4. Listar tarefas de novo
curl -s http://localhost:30080/tasks | jq 'length'
# 0  ← dados sumiram
```

**Por que aconteceu:**

- O Pod do Postgres usa `emptyDir` para `/var/lib/postgresql/data`.
- `emptyDir` vive **enquanto o Pod vive**. Pod novo → `emptyDir` novo →
  banco vazio.
- A API, por sua vez, sobreviveu: roda em **2 réplicas** sem estado, então
  matar 1 Pod não derruba o serviço (HA de API funciona). O problema é só
  no estado (Postgres).

**Saída real:**

- Usar **PersistentVolumeClaim (PVC)** + StorageClass — mas em Kind é
  apenas hostPath local (ainda frágil).
- Em produção: **RDS** (ver [`09-deploy-manual-aws.md`](09-deploy-manual-aws.md) §7).

---

## 10. Cleanup

```bash
# Apaga só os recursos da app (cluster continua de pé)
kubectl delete -k infra/k8s/

# Apaga o cluster inteiro (libera CPU/RAM do host) — recomendado ao fim
kind delete cluster --name cloudtask
```

---

## 11. Troubleshooting

| Erro | Causa | Fix |
| --- | --- | --- |
| `error: error loading config file ... no such file` | rodou comando fora da raiz do repo | rode no diretório onde está `infra/k8s/` |
| Pod `ErrImagePull` `cloudtask-api:prod` | esqueceu `kind load docker-image` | `docker build --target prod -t cloudtask-api:prod . && kind load docker-image cloudtask-api:prod --name cloudtask` |
| Pod `CrashLoopBackOff` + log `ModuleNotFoundError: No module named 'app'` | carregou a imagem `dev` (sem código embutido) no cluster | rebuild com `--target prod` (ver §3): `docker build --target prod -t cloudtask-api:prod . && kind load docker-image cloudtask-api:prod --name cloudtask` |
| Pod `Init:CrashLoopBackOff` (init container) | Postgres travou no startup | `kubectl logs -n cloudtask pod/postgres-... -c postgres` — provavelmente senha mal codificada em base64 |
| `dial tcp ...:30080: connect: connection refused` | `extraPortMappings` faltou no kind-config | recrie o cluster com `--config infra/k8s/kind-config.yaml` |
| API responde 500 ao chamar `/tasks` | `DATABASE_URL` errada no Secret | confira o base64; veja log: `kubectl logs -n cloudtask -l app=api` |
| `kubectl: command not found` no host | só está no devcontainer | use `kubectl` do devcontainer ou instale no host (apt/brew/choco) |
| `kind delete cluster` reclama de "not found" | já foi apagado | ignorar |

---

## 12. O que mudou em relação à Aula 5

| Antes (Aula 5) | Depois (Aula 6) |
| --- | --- |
| API e DB rodavam em `docker-compose` no devcontainer | API e DB rodam em Pods no cluster Kind |
| Configuração via `.env` montado por bind mount | Configuração via ConfigMap + Secret |
| 1 instância da API | 2 réplicas, com Service balanceando |
| `curl localhost:8000` | `curl localhost:30080` (NodePort do Service) |
| `docker compose down` apaga tudo | `kubectl delete -k infra/k8s/` + `kind delete cluster` |

---

## Próximos passos

| Quero... | Vá em |
| --- | --- |
| Deployar na nuvem (EKS) | [`09-deploy-manual-aws.md`](09-deploy-manual-aws.md) §5 |
| Comparar Kind × EKS × Fargate | [`../conceitos/infra-aws-minima-por-semana.md`](../conceitos/infra-aws-minima-por-semana.md) |
| Resolver problemas mais gerais | [`99-troubleshooting.md`](99-troubleshooting.md) |
