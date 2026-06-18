# Prática 99 — Troubleshooting

> **Catálogo de erros conhecidos** + diagnóstico + fix. Não é uma prática
> sequencial — consulte quando bater algum erro.
>
> Está organizado por **sintoma**.

---

## Índice rápido

- [Docker / Compose](#docker--compose)
- [Devcontainer](#devcontainer)
- [Banco PostgreSQL](#banco-postgresql)
- [API / Swagger](#api--swagger)
- [Testes (pytest)](#testes-pytest)
- [Uploads (S3 ou local)](#uploads-s3-ou-local)
- [AWS / credenciais](#aws--credenciais)
- [Kubernetes / EKS / HPA (Aulas 6, 8, 9)](#kubernetes--eks--hpa-aulas-6-8-9)
- [ECS / Fargate (deploy de container)](#ecs--fargate-deploy-de-container)
- [DynamoDB / eventos (Aula 10)](#dynamodb--eventos-aula-10)
- [💸 Custos que escapam](#-custos-que-escapam-sempre-confira-ao-destruir)
- [Git / branches](#git--branches)
- [Windows / WSL específico](#windows--wsl-específico)

---

## Docker / Compose

### `Cannot connect to the Docker daemon`

**Causa:** Docker Desktop não está rodando.
**Fix:** abra Docker Desktop, espere o ícone ficar verde, tente de novo.

### `port is already allocated` (8000 ou 5432)

**Causa:** outro serviço usa a porta.
**Fix opções:**

```bash
# 1. Descobrir quem está usando:
# Windows:
netstat -ano | findstr :5432
# Linux/Mac:
lsof -i :5432

# 2. Parar o conflitante OU mudar a porta do projeto no .env:
echo "POSTGRES_PORT=5433" >> .env
docker compose down && docker compose up -d
```

### `docker compose ps` vazio dentro do devcontainer

**Causa:** dentro do container, `pwd` é `/app`, project name vira `app`.
**Fix:**

```bash
docker compose -p cloudtaskaisaas ps
# ou:
docker ps --filter "label=com.docker.compose.project=cloudtaskaisaas"
```

---

## Devcontainer

### Build falha com `moby-cli not found`

**Causa:** feature `docker-outside-of-docker` tentou instalar moby-cli em
Debian trixie (não tem).
**Fix:** já corrigido — `"moby": false` no `devcontainer.json`. Se reapareceu,
confirme o JSON.

### Build falha em `nvm` / `source: not found`

**Causa:** feature de Node usa `source` (não existe em dash).
**Fix:** já corrigido — Node vem via `apt install nodejs npm` no Dockerfile
dev. Confirme o `Dockerfile`.

### `chown: invalid group: 'appuser:appuser'`

**Causa:** grupo se chamava `appgroup`.
**Fix:** já corrigido — `Dockerfile` cria `appuser:appuser`.

### Mount com path estranho (`HOME` + `USERPROFILE` concatenados)

**Causa:** `${localEnv:HOME}${localEnv:USERPROFILE}` se as duas variáveis
existem.
**Fix:** use **apenas uma** (`USERPROFILE` no Windows, `HOME` no
mac/Linux). Já corrigido em `devcontainer.json`.

### Prompt aparece sem cores / sem timestamp

**Causa:** `.zshrc` não foi copiado pra `~/`.
**Fix:**

```bash
cp /app/.devcontainer/.zshrc ~/.zshrc
exec zsh
```

### Sticky scroll não funciona

**Causa:** `terminal.integrated.shellIntegration.enabled` está `false`.
**Fix:** confira `devcontainer.json → customizations.vscode.settings`:

```json
"terminal.integrated.shellIntegration.enabled": true,
"terminal.integrated.stickyScroll.enabled": true,
"terminal.integrated.shellIntegration.decorationsEnabled": "both"
```

E o `.zshrc` precisa ter os marcadores OSC 633.

---

## Banco PostgreSQL

### `could not connect to server: Connection refused`

**Causa:** container `db` ainda subindo, ou parado.
**Fix:**

```bash
docker compose ps db                 # State deve ser "Up (healthy)"
docker compose up -d db              # se estiver parado
docker compose logs -f db            # ver logs
```

### `FATAL: password authentication failed`

**Causa:** `.env` divergente do esperado pelo container.
**Fix:** confira `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` no `.env`
batem com `DATABASE_URL`.

### `relation "tasks" does not exist`

**Causa:** banco vazio e API não subiu antes (não rodou `create_all`).
**Fix:** suba a API uma vez:

```bash
docker compose up -d api
curl http://localhost:8000/health    # força o startup
```

### Teste de pytest "vê" dados do dev (não isolado)

**Causa:** fixture sem TRUNCATE ou sem rollback.
**Fix:** já tratado em `tests/conftest.py` (TRUNCATE + savepoint + rollback no
finally). Se acontecer, reveja se `db_session` está usando essa fixture.

---

## API / Swagger

### `ModuleNotFoundError: No module named 'boto3'` (ou outro)

**Causa:** trocou de branch e não fez rebuild — imagem antiga não tem a lib
nova.
**Fix:**

```bash
# Sair do devcontainer (Reopen Folder Locally)
# F1 → Dev Containers: Rebuild Container
```

### Swagger não abre — só "Invalid HTTP request"

**Causa:** acessou `https://localhost:8000` em vez de `http://`. Dev é
**HTTP**, não HTTPS.
**Fix:** use `http://localhost:8000/docs`.

### `307 Temporary Redirect` infinito

**Causa:** `force_https=True` + `behind_proxy=False` no `.env` rodando local
sem proxy.
**Fix:** desligue `FORCE_HTTPS=false` em dev.

### Endpoint nunca aparece no Swagger

**Causa:** router não foi registrado.
**Fix:** confira `app/main.py` → `app.include_router(routes_XXX.router)`.

---

## Testes (pytest)

### Mudei o código/teste mas o resultado do container isolado não muda

**Causa:** você rodou o container isolado **sem `--build`**:
```bash
docker compose -p cloudtask-test -f docker-compose.yml -f docker-compose.test.yml run --rm api
```
O target `test` faz `COPY` do código para **dentro** da imagem (sem bind mount).
Sem `--build`, o Compose reaproveita a imagem em cache com o código **antigo** →
você testa uma versão **fóssil** (a correção "não faz efeito"; um teste que você
quebrou continua passando).

**Fix:** sempre acrescente `--build` nesse caminho:
```bash
docker compose -p cloudtask-test -f docker-compose.yml -f docker-compose.test.yml run --build --rm api
```
> O caminho rápido (`pytest`/`tv` **dentro** do devcontainer) NÃO sofre disso —
> ele usa o código por **volume** (target `dev`), enxergando suas edições na hora.

### `41 passed`, mas dados do dev sumiram

**Causa:** TRUNCATE rodou FORA de transação (`begin` faltando).
**Fix:** já tratado. Confira `tests/conftest.py` se replicou em outra branch.

### Warnings de Starlette (deprecation)

**Causa:** lib futura.
**Fix:** já tratado por `addopts = "-ra -q -p no:warnings"` em
`pyproject.toml`. Se persistir, **rebuild** o devcontainer (imagem cacheada).

### Pytest não acha `tests/`

**Causa:** rodando de pasta errada.
**Fix:** rode na raiz do projeto. Ou:

```bash
pytest --rootdir=/app /app/tests/
```

---

## Uploads (S3 ou local)

### `413 Request Entity Too Large` com arquivo pequeno

**Causa:** proxy intermediário.
**Fix:** em dev local não tem proxy. Confira `ls -la arquivo` — tamanho real.

### `storage_mode` ainda diz `"local"` após mudar `.env`

**Causa:** `restart` não recarrega `.env`; só `create`.
**Fix:**

```bash
docker compose down && docker compose up -d
```

### `404 Arquivo não encontrado` ao baixar do S3

**Causa:** prefixo gerado é único, você usou nome errado.
**Fix:** use o `filename` da resposta do POST. Liste no bucket:

```bash
aws s3 ls s3://$BUCKET/
```

---

## AWS / credenciais

### `Unable to locate credentials`

**Causa:** `~/.aws/credentials` vazio ou não montado.
**Fix:**

1. Cole credenciais do Learner Lab em `~/.aws/credentials` no **host**.
2. Confirme mount no `devcontainer.json`:
   ```json
   "source=${localEnv:USERPROFILE}/.aws,target=/home/appuser/.aws,..."
   ```
3. Dentro do container: `cat ~/.aws/credentials` deve mostrar conteúdo.

### `The security token included in the request is expired`

**Causa:** sessão do Learner Lab passou de 4h.
**Fix:** abra Learner Lab novo, cole credenciais frescas em `~/.aws/credentials`.

### `Could not connect to the endpoint URL`

**Causa:** `AWS_REGION` errada ou rede do container sem internet.
**Fix:**

```bash
docker compose exec api ping -c 2 s3.amazonaws.com
# se falhar: docker network ls, docker compose down && up
```

---

## Kubernetes / EKS / HPA (Aulas 6, 8, 9)

### HPA mostra `TARGETS: <unknown>/...` e não escala

**Causa:** o HPA não consegue ler a métrica de CPU. Três motivos comuns:
1. **metrics-server** não está pronto (ou nem instalado).
2. O Deployment **não declara `resources.requests.cpu`** (é a base do cálculo:
   utilização = uso ÷ request — sem request não há porcentagem).
3. O metrics-server subiu, mas ainda **não completou o 1º ciclo de coleta**
   (espere 1–2 min).

**Fix:**
```bash
kubectl top nodes            # tem que listar CPU/MEM; se der erro, é o metrics-server
kubectl get deploy metrics-server -n kube-system
# confirme que o Deployment-alvo tem requests.cpu (no projeto: deployment-eks.yaml)
```

### `kubectl top` dá erro / metrics-server não coleta

**No EKS:** prefira o **addon gerenciado** (`eksctl`/console já instala). **NÃO**
aplique também o manifesto upstream (`components.yaml`) — vira **dois**
metrics-server disputando o `APIService v1beta1.metrics.k8s.io` (erro de campo
imutável) e quebra.

**No Kind (local):** o manifesto upstream falha no TLS do kubelet. Aplique o
patch:
```bash
kubectl -n kube-system patch deploy metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```
> ⚠️ `--kubelet-insecure-tls` é só para o ambiente local do Kind, nunca em produção.

### Pod `ErrImagePull` / `ImagePullBackOff` da imagem `cloudtask-api`

**Causa:** o cluster não encontra a imagem.
- **Kind:** esqueceu de carregar a imagem no cluster.
  ```bash
  docker build --target prod -t cloudtask-api:prod .
  kind load docker-image cloudtask-api:prod --name cloudtask
  ```
- **EKS:** a imagem não está no ECR ou o nome/tag está errado. Confira
  `aws ecr list-images --repository-name cloudtask-api`.

### Pod `CreateContainerConfigError`

**Causa:** o Pod referencia um **Secret/ConfigMap que não existe**. No projeto,
o `kustomization.yaml` pode estar com `- secret.yaml` comentado, ou o
`secret.yaml` não foi criado a partir do `secret.example.yaml`.
**Fix:** crie o Secret (ver `infra/k8s/secret.example.yaml`) e descomente a linha
no `kustomization.yaml`, ou aplique via `kubectl create secret generic ...`.

### Pod `Init:0/1` travado (`wait-for-postgres`)

**Causa:** o init container espera o Postgres responder e ele não sobe.
**Fix:** `kubectl logs <pod> -c <postgres> -n cloudtask` — geralmente senha mal
codificada em base64 no Secret, ou o Pod do banco em `Pending`.

### `kubectl get nodes` vem vazio no EKS (modo quick / Auto Mode)

**Causa:** **não é erro.** No Auto Mode os nós são provisionados **sob demanda**
quando o 1º pod precisa. Suba um workload e os nós aparecem em ~1–2 min.

### Console do EKS mostra "Resources" vazio (mas os addons aparecem)

**Causa:** o principal que abre o console **não tem acesso RBAC** ao cluster (o
admin é concedido só a quem **criou** o cluster). Os addons aparecem porque são
API da AWS, não Kubernetes.
**Fix:** crie uma **access entry** para o seu principal:
```bash
aws eks create-access-entry --cluster-name <CLUSTER> --region us-east-1 \
  --principal-arn <SEU_ARN>
aws eks associate-access-policy --cluster-name <CLUSTER> --region us-east-1 \
  --principal-arn <SEU_ARN> --access-scope type=cluster \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
```
> ⚠️ A AWS costuma **rejeitar** o ARN de conta-root (`...:root`). Use um IAM
> user/role, ou abra o console com o mesmo principal que criou o cluster.

### `Service type=LoadBalancer` — `EXTERNAL-IP` em `<pending>` ou "Empty reply"

- **`<pending>` por muito tempo:** no Kind não há cloud provider que crie ELB —
  use `NodePort`/`port-forward`. No EKS, espere ~2 min.
- **"Empty reply from server" / curl não conecta:** no **Auto Mode** o ELB
  clássico às vezes não marca o alvo como *healthy* a tempo. Para a demonstração,
  o que importa é que o **hostname externo foi gerado**.
- **URL correta:** use o hostname **sem porta** (porta **80** implícita, que é o
  `port` do Service) — **não** `:8080`/`:31702` (essas são port-forward/NodePort,
  não o listener do ELB). Achar o DNS: **Console → EC2 → Load Balancers → DNS name**
  ou `kubectl get svc <svc> -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'`.

### `eksctl create cluster` falha com erro de IAM (Learner Lab)

**Causa:** o Learner Lab não deixa criar roles novas.
**Fix:** use a `LabRole` existente ou o cluster pré-criado pelo professor.

---

## ECS / Fargate (deploy de container)

### Task sobe e cai em loop (`EssentialContainerExited`, exit code 3)

**Causa nº1:** a API CloudTask **exige Postgres** desde a Aula 3. No startup o
`lifespan` roda `create_all()`; se a `DATABASE_URL` não apontar para um banco
alcançável, o **uvicorn sai com exit 3** ("Application startup failed") e a task
reinicia. Subir a API **sozinha** (sem container de banco nem RDS) sempre quebra.
**Fix:** use **2 containers na mesma task** (api + db), `DATABASE_URL=...@localhost:5432`,
`dependsOn db condition HEALTHY` — ver `infra/aws/task-def-fargate-api-db.json`.

### Placeholder não substituído na `DATABASE_URL`

**Causa:** `DATABASE_URL=postgresql://USER:SENHA@HOST:5432/...` com `USER`/`SENHA`/
`HOST` literais (nunca trocados) → o app tenta resolver o host `HOST` e falha.
**Fix:** preencha com valores reais (ou `localhost` no caso 2-container).

### Container "morre mudo" (sem nenhum log no CloudWatch)

**Causa:** a task definition **não tem `logConfiguration`** (awslogs). O container
falha mas não há para onde logar.
**Fix:** adicione `logConfiguration` (driver `awslogs`, `awslogs-create-group: true`)
em cada container — sem isso, impossível diagnosticar.

### `ResourceInitializationError: unable to pull secrets or registry auth`

**Causa:** a task está em **subnet privada sem NAT** (sem rota para a internet) →
não puxa imagem do ECR nem lê o Secret → morre antes de logar.
**Fix:** use **subnet pública** + `assignPublicIp=ENABLED`.

### Service não existe mais após apagar o cluster

**Causa:** deletar o cluster ECS remove serviços/tasks, mas **as task definitions
sobrevivem** (recurso à parte). Para recriar, registre o service de novo.

---

## DynamoDB / eventos (Aula 10)

### `GET /events` retorna 500 no modo local

**Causa:** sem permissão de escrita no caminho `LOCAL_EVENTS_FILE`
(ex.: `./local_events/events.json`).
**Fix:** confira se a pasta existe e é gravável pelo usuário do container.

### `ResourceNotFoundException` no modo DynamoDB

**Causa:** a tabela não foi criada, ou o nome/região não batem.
**Fix:**
```bash
aws dynamodb create-table --table-name cloudtask-events \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1
# confira DYNAMODB_TABLE_NAME e AWS_REGION no .env
```

### `AccessDenied` no DynamoDB (AWS Academy)

**Causa:** a role `voclabs` do Learner Lab pode limitar o DynamoDB.
**Fix:** use o modo **`EVENT_STORE_MODE=local`** (JSON), que completa a Aula 10
sem AWS.

### Criar tarefa não gera evento (`task.created`)

**Causa:** o event store apontado por `EVENT_STORE_MODE` está fora do ar (arquivo
sem permissão, ou DynamoDB inacessível). O CRUD **não quebra** — o evento é
secundário e vira só um *warning* no log.
**Fix:** veja o log da API; ajuste o backend ou volte para o modo `local`.

---

## 💸 Custos que escapam (sempre confira ao destruir)

Ao apagar EKS/Fargate, alguns recursos **continuam cobrando** se ficarem órfãos.
Rode o *sweep* e zere tudo:

```bash
echo "== EKS ==";       aws eks list-clusters --region us-east-1 --query clusters --output text
echo "== EC2 ==";       aws ec2 describe-instances --filters "Name=instance-state-name,Values=running,pending" --query "Reservations[].Instances[].InstanceId" --output text --region us-east-1
echo "== LB v2 ==";     aws elbv2 describe-load-balancers --query "LoadBalancers[].DNSName" --output text --region us-east-1
echo "== LB clássico =="; aws elb describe-load-balancers --query "LoadBalancerDescriptions[].DNSName" --output text --region us-east-1
echo "== NAT GW ==";    aws ec2 describe-nat-gateways --filter "Name=state,Values=available,pending" --query "NatGateways[].NatGatewayId" --output text --region us-east-1
echo "== EIP solto =="; aws ec2 describe-addresses --query "Addresses[?AssociationId==null].PublicIp" --output text --region us-east-1
echo "== EBS livre =="; aws ec2 describe-volumes --query "Volumes[?State=='available'].VolumeId" --output text --region us-east-1
```

| Vilão | Por que cobra | Como apagar |
| --- | --- | --- |
| **Service LoadBalancer** órfão | ELB fica de pé após o cluster sumir | apague o `Service` **antes** do cluster |
| **NAT Gateway** | ~$0,045/h, 24/7 (quick-create às vezes cria) | `aws ec2 delete-nat-gateway --nat-gateway-id <ID>` |
| **Elastic IP solto** | EIP não associado cobra | `aws ec2 release-address --allocation-id <ID>` |
| **EBS disponível** | volume órfão de nó deletado | `aws ec2 delete-volume --volume-id <ID>` |
| **Cluster EKS** | $0,10/h só por existir + nós | `eksctl delete cluster` ou Console → Delete |

> **Ordem segura:** Service LoadBalancer → workloads → cluster → sweep dos órfãos.

---

## Git / branches

### 70 arquivos aparecem como modificados após mudar de branch

**Causa:** CRLF (Windows) ↔ LF (Linux container) + `fileMode` ativo.
**Fix:**

```bash
# Já tratado: .gitattributes + git config core.fileMode false + autocrlf
# Se persistir:
git rm --cached -rf .
git reset --hard
```

### Branch trocada mas Swagger quebrado (`ModuleNotFoundError`)

**Causa:** imagem do devcontainer congelada na branch antiga.
**Fix:** **Rebuild Container** sempre que trocar de semana.

---

## Windows / WSL específico

### `mount: permission denied` ao iniciar devcontainer

**Causa:** pasta `~/.aws` ou `~/.kube` do host não existe.
**Fix:** crie no host:

```powershell
mkdir $env:USERPROFILE\.aws -Force
mkdir $env:USERPROFILE\.kube -Force
```

### Editor mostra `^M` no final das linhas

**Causa:** arquivos checados com CRLF.
**Fix:** `.gitattributes` já força LF. Re-clone ou:

```bash
git rm --cached -rf .
git reset --hard
```

### Docker Desktop não inicia (WSL2)

**Causa:** WSL2 desativado ou kernel antigo.
**Fix:**

```powershell
wsl --update
wsl --set-default-version 2
```

---

## Quando nada funciona

1. **Salve seu trabalho** (`git add . && git commit -m "WIP"`).
2. **Rebuild completo:**
   ```bash
   docker compose down -v
   docker system prune -af --volumes
   ```
   ⚠️ Apaga **tudo** do Docker (imagens, volumes, redes). Recria do zero.
3. **Reabrir devcontainer** → `F1 → Rebuild Container`.

Se ainda não funcionou, abra issue no GitHub com:

- Aula / branch.
- Comando exato que rodou.
- Saída completa do erro.
- SO (Windows 11? macOS? Linux?).
- Versões: `docker --version`, `git --version`, `code --version`.
