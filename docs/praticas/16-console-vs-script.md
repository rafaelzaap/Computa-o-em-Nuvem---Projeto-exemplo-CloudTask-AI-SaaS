# Prática 16 — Console vs Script: fazendo na mão para sentir a diferença

> **Objetivo:** criar **pelo Console da AWS (cliques)** alguns recursos que os
> scripts da disciplina sobem com **um comando**, para você sentir **na prática
> quanto tempo e quantos passos** custa fazer "no manual". É a razão de existirem
> CLI, scripts e IaC (CDK na Semana 6).
>
> **Quando:** Semana 5 (ou sempre que quiser entender o valor da automação).
>
> **Como usar este doc:** você não precisa concluir todos os exemplos — pode só
> acompanhar 1 ou 2. Se for fazer, **cronometre cada exemplo**: a lentidão é
> justamente o que queremos que você perceba.
>
> ⚠️ **Custo:** se você criar de verdade um EKS pelo console, ele **cobra por
> hora**. Só faça se for **apagar logo em seguida** (este doc mostra como apagar
> tudo). Para DynamoDB/Budget o custo é praticamente zero. Os exemplos marcados
> com 🟢 são baratos; os 🔴 cobram — atenção redobrada.

---

## Como ler as tabelas de comparação

Em cada exemplo você verá:

- **Console (na mão):** a sequência de telas/cliques + tempo aproximado.
- **Script/CLI (1 comando):** o equivalente já pronto na disciplina.
- **Veredito:** passos e minutos de um lado vs do outro.

> "Passos" = telas/campos que exigem decisão ou digitação. Não conta esperar.

---

## Exemplo 1 — 🟢 Tabela DynamoDB (barato)

### No Console (na mão)

1. Console AWS → busque **DynamoDB** → abra.
2. **Create table**.
3. **Table name:** `cloudtask-events-console`.
4. **Partition key:** `id` — tipo **String**.
5. (deixe sort key vazio).
6. **Table settings:** escolha **Customize settings** (senão não vê as opções).
7. **Capacity mode:** troque para **On-demand** (= `PAY_PER_REQUEST`).
8. Role a página revisando *encryption*, *tags*, etc.
9. **Create table**.
10. Espere o status sair de *Creating* para *Active* (~30–60 s).
11. Abra a tabela → **Explore items** → **Create item** para inserir 1 evento
    manual (preencha `id`, depois *Add new attribute* → String `event_type`,
    de novo para `message`, de novo para `created_at`… um campo por vez).

**Tempo real:** ~3 a 5 min só para a tabela + ~2 min por item manual.
**Passos:** ~11 telas/campos + N por item.

### Com a CLI (1 comando)

```bash
aws dynamodb create-table --table-name cloudtask-events \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1
```

E inserir um item:

```bash
aws dynamodb put-item --table-name cloudtask-events --item '{
  "id":{"S":"evt-1"},"event_type":{"S":"task.created"},
  "message":{"S":"teste"},"created_at":{"S":"2026-01-01T00:00:00Z"}
}'
```

> Na disciplina nem isso você digita: a **app** cria o item sozinha ao chamar
> `POST /events` (ver [`15-eventos-dynamodb.md`](15-eventos-dynamodb.md)).

### Veredito

| | Console | CLI |
| --- | --- | --- |
| Criar tabela | ~11 passos, 3–5 min | 1 comando, ~5 s |
| Inserir item | N campos por item | 1 comando (ou automático pela app) |
| Reproduzir em outra conta | refazer tudo na mão | colar o mesmo comando |
| Risco de erro | digitar tipo errado, esquecer on-demand | nenhum (texto fixo) |

---

## Exemplo 2 — 🔴 Cluster EKS (este COBRA por hora — só faça se for apagar logo)

Este é o exemplo em que a diferença entre console e script fica mais gritante.

> ⚠️ **Limite do console:** o console cria o **cluster** (e, no **modo quick /
> Auto Mode**, já instala o **metrics-server**), mas **PARA AÍ**. Subir
> container (Deployment), Service e HPA **não tem tela de cliques** — o EKS não
> tem UI de workload. A partir daí é **só `kubectl`**, exatamente o que o script
> faz por baixo. Você nem precisa instalar nada na sua máquina: use o
> **AWS CloudShell** (o terminal embutido no próprio console — ícone `>_` no
> topo da página). Ver [§Parte 2 abaixo](#parte-2--depois-do-cluster-só-pelo-terminal-aws-cloudshell).

### Parte 1 — Criar o cluster no Console (na mão)

> Pré-requisito que o console **não** cria para você: **roles IAM** e **VPC**.
> Você precisa ter (ou criar à parte):
> - uma **IAM role do cluster** (com `AmazonEKSClusterPolicy`);
> - uma **IAM role dos nós** (com `AmazonEKSWorkerNodePolicy`,
>   `AmazonEC2ContainerRegistryReadOnly`, `AmazonEKS_CNI_Policy`);
> - uma **VPC com subnets** em 2+ zonas.

Criar as **roles IAM** (na mão, antes):

1. IAM → Roles → **Create role** → *AWS service* → **EKS** → *EKS - Cluster* →
   Next → Create (role do cluster).
2. IAM → Roles → **Create role** → *EC2* → Next → anexe as **3 policies**
   acima, uma por uma (buscar + marcar) → Next → nomeie → Create (role dos nós).

Criar o **cluster**:

3. Console → **EKS** → **Add cluster → Create**.
4. **Name:** `cloudtask-eks-console`.
5. **Kubernetes version:** escolher.
6. **Cluster service role:** selecionar a role do passo 1.
7. **Secrets encryption / tags:** revisar.
8. **Networking:** escolher a **VPC**, as **subnets** (marcar cada uma),
   **security group**, e *cluster endpoint access* (Public).
9. **Add-ons:** revisar vpc-cni, kube-proxy, CoreDNS, metrics-server (versões).
10. **Review and create** → **Create**.
11. **Espere ~10–15 min** o cluster ficar *Active*.

Criar o **node group** (os nós só vêm depois, à parte):

12. Abra o cluster → aba **Compute** → **Add node group**.
13. **Name:** `ng-console`.
14. **Node IAM role:** selecionar a role dos nós (passo 2).
15. **Instance type:** `t3.small`, **Disk**, **Scaling** (min/max/desired = 2).
16. **Subnets:** marcar.
17. **Create** → **Espere ~3–5 min** os nós entrarem em *Ready*.

**Tempo real:** **~30–45 min de cliques** + ~20 min de espera. ~17 passos +
as roles. Um erro em qualquer subnet/role → mensagem obscura e recomeça.

> 🟦 **Atalho do console — modo "quick" (Auto Mode):** ao criar o cluster, a AWS
> oferece um fluxo rápido que **cria roles/VPC/addons sozinho** e liga o
> **Auto Mode** (sem node group fixo — os nós são provisionados **sob demanda**
> quando o 1º pod precisa, e o **metrics-server já vem instalado**). Isso encurta
> a Parte 1, mas **não muda a Parte 2**: workload/HPA continuam só por `kubectl`.

### Parte 2 — Depois do cluster: só pelo terminal (AWS CloudShell)

O console **não cria** Deployment/Service/HPA. Faça igual ao script, mas na mão,
pelo **AWS CloudShell** (ícone `>_` no topo do console — já vem com `aws` e
`kubectl`, sem instalar nada).

**1. Conectar o kubectl ao cluster:**
```bash
aws eks update-kubeconfig --name <NOME-DO-CLUSTER> --region us-east-1
kubectl get nodes
```
> 🟦 **Auto Mode:** `get nodes` pode vir **vazio** até existir workload — o nó é
> criado sob demanda quando o 1º pod precisa. É normal.

**2. Subir o app que queima CPU (php-apache) + Service:**
```bash
kubectl apply -f - <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: php-apache
spec:
  replicas: 1
  selector:
    matchLabels: { run: php-apache }
  template:
    metadata:
      labels: { run: php-apache }
    spec:
      containers:
        - name: php-apache
          image: registry.k8s.io/hpa-example
          ports: [{ containerPort: 80 }]
          resources:
            requests: { cpu: 200m }   # BASE do cálculo do HPA
            limits:   { cpu: 500m }
---
apiVersion: v1
kind: Service
metadata:
  name: php-apache
  labels: { run: php-apache }
spec:
  ports: [{ port: 80 }]
  selector: { run: php-apache }
YAML
kubectl rollout status deploy/php-apache --timeout=180s
```
> 🟦 **Auto Mode:** aqui ele provisiona o nó (~1–2 min) antes do pod ficar `Running`.

**3. Criar o HPA (cpu 50%, 1→10):**
```bash
kubectl autoscale deployment php-apache --cpu=50% --min=1 --max=10
kubectl get hpa
kubectl top pods        # confirma que a métrica de CPU aparece (metrics-server ok)
```

**4. Gerar carga (deixe rodando) e observar em outra aba:**

Terminal A (observar) — abra uma 2ª aba do CloudShell:
```bash
kubectl get hpa -w
```
Terminal B (carga):
```bash
kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never \
  -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://php-apache; done"
```
Em ~1–3 min: `TARGETS` passa de 50% → `REPLICAS` sobe 1→…→10. `Ctrl+C` no
Terminal B → após ~5 min volta a 1.

**5. (Opcional) Ver no navegador + gerar um link externo (LoadBalancer):**

O `php-apache` é só um gerador de CPU — a página responde apenas `OK!` (o mesmo
texto que inundou o load generator). Mesmo assim, é didático **ver o link externo
ser gerado**.

Por padrão o Service `php-apache` é **`ClusterIP`** (só acessível DENTRO do
cluster). Duas formas de ver de fora:

**Opção A — `port-forward` (grátis, instantâneo):**
```bash
kubectl port-forward svc/php-apache 8080:80
# abra http://localhost:8080  → aparece "OK!"   (Ctrl+C encerra)
```
> ⚠️ **No CloudShell isso NÃO abre no seu navegador:** o `localhost` é a máquina
> do CloudShell (remota), não o seu PC. Use `curl http://localhost:8080` ali
> mesmo para provar que responde. Para abrir no SEU navegador, rode o
> `port-forward` num terminal **da sua máquina** (com `kubectl` configurado).

**Opção B — `LoadBalancer` (cria um ELB de verdade, ~2 min, CUSTA):**
```bash
kubectl patch svc php-apache -p '{"spec":{"type":"LoadBalancer"}}'
kubectl get svc php-apache -w     # espere a coluna EXTERNAL-IP virar um hostname
```
A coluna **EXTERNAL-IP** vira um **hostname gerado** pela AWS, tipo:
```
a17c2111a80b548b6aafe2a89685443e-918798177.us-east-1.elb.amazonaws.com
```

**Como montar a URL (qual porta?):**
- Use o hostname **SEM porta** → o navegador assume **:80**, que é a porta que o
  Service expõe (`port: 80`):
  ```bash
  curl http://a17c2111a80b...elb.amazonaws.com          # (porta 80 implícita)
  # ou explicitando:  curl http://a17c...elb.amazonaws.com:80
  ```
- **NÃO** use `:8080` nem `:31702` — essas são portas internas (port-forward /
  NodePort), o **listener do ELB é só a 80**. Por isso aqueles davam
  `Failed to connect`.

**Onde achar esse mesmo hostname/IP no Console:**
- **EC2** (não no EKS!) → menu esquerdo **Load Balancers** → selecione o LB
  (o nome começa com o hash do Service) → aba **Description** → campo
  **DNS name**. É o mesmo hostname do `EXTERNAL-IP`.
- Atalho equivalente por terminal:
  ```bash
  kubectl get svc php-apache -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; echo
  ```

> 🩺 **"Empty reply from server" é esperado aqui.** No **Auto Mode**, o ELB
> clássico às vezes não marca o alvo como *healthy* a tempo → a página não
> carrega. **Para a aula tudo bem:** o ponto é mostrar que **o link/IP é gerado
> automaticamente**, não servir conteúdo. Quem quiser uma UI real no navegador:
> exponha a **própria CloudTask** (`/docs` Swagger) via LoadBalancer — aí tem tela.

**6. Limpar — a ORDEM importa (ELB primeiro, cluster por último):**

> 🔴 Se você criou o Service `LoadBalancer` (Opção B), **apague-o ANTES do
> cluster**. Senão o ELB fica **órfão cobrando** depois que o cluster some.

```bash
# 6.1 — CRÍTICO: remover o Service type=LoadBalancer deleta o ELB junto
kubectl delete svc php-apache  --ignore-not-found
kubectl delete hpa php-apache  --ignore-not-found
kubectl delete deploy php-apache --ignore-not-found
kubectl delete pod load-generator --ignore-not-found

# 6.2 — confirmar que o ELB sumiu (espere ~1 min)
kubectl get svc
aws elb   describe-load-balancers --query "LoadBalancerDescriptions[].DNSName" --output text --region us-east-1
aws elbv2 describe-load-balancers --query "LoadBalancers[].DNSName"            --output text --region us-east-1
# tudo vazio = ELB liberado
```

```bash
# 6.3 — apagar o cluster. Criado pelo console (quick)? O mais seguro é deletar
#        PELO CONSOLE (resolve dependências): EKS → seu cluster → Delete → digite o nome.
#        Por CLI (troque <CLUSTER>):
aws eks list-nodegroups --cluster-name <CLUSTER> --region us-east-1
# (para cada NG) aws eks delete-nodegroup --cluster-name <CLUSTER> --nodegroup-name <NG> --region us-east-1
aws eks delete-cluster --name <CLUSTER> --region us-east-1
```

```bash
# 6.4 — sweep de billing (nada pode sobrar cobrando)
echo "== EKS ==";       aws eks list-clusters --region us-east-1 --query clusters --output text
echo "== EC2 ==";       aws ec2 describe-instances --filters "Name=instance-state-name,Values=running,pending" --query "Reservations[].Instances[].InstanceId" --output text --region us-east-1
echo "== LB v2 ==";     aws elbv2 describe-load-balancers --query "LoadBalancers[].DNSName" --output text --region us-east-1
echo "== NAT GW ==";    aws ec2 describe-nat-gateways --filter "Name=state,Values=available,pending" --query "NatGateways[].NatGatewayId" --output text --region us-east-1
echo "== EIP solto =="; aws ec2 describe-addresses --query "Addresses[?AssociationId==null].PublicIp" --output text --region us-east-1
echo "== EBS livre =="; aws ec2 describe-volumes --query "Volumes[?State=='available'].VolumeId" --output text --region us-east-1
```

> ⚠️ **Atenção a NAT Gateway e EIP solto:** o *quick create* do console às vezes
> cria uma VPC **com NAT Gateway** (~$0,045/h cada, 24/7 — o item mais traiçoeiro).
> Se o sweep listar algum:
> ```bash
> aws ec2 delete-nat-gateway --nat-gateway-id <NAT_ID> --region us-east-1
> aws ec2 release-address     --allocation-id  <ALLOC_ID> --region us-east-1   # EIP solto
> ```
> Tudo vazio = zero cobrança.

> 💡 **Repare:** a Parte 1 (console) levou ~30 min de cliques; a Parte 2 **não
> tinha botão nenhum** — foi 100% terminal. Ou seja, mesmo "fazendo no console",
> metade do trabalho real **só existe via `kubectl`**. Compare com o `eksctl`
> da próxima seção, que faz **as duas partes de uma vez**, em um comando.

### Com o eksctl (1 comando)

```bash
eksctl create cluster \
  --name cloudtask-eks --region us-east-1 \
  --node-type t3.small --nodes 2 --managed
```

Esse **único comando** cria: VPC + subnets + IGW + roles IAM + cluster +
node group + addons + kubeconfig. É o mesmo comando que você já usou na
[`12-eks-deploy.md`](12-eks-deploy.md).

### Veredito

| | Console + CloudShell | eksctl + script |
| --- | --- | --- |
| Roles IAM | criar 2 na mão, anexar 4 policies (ou quick mode) | criadas sozinhas |
| VPC/subnets/IGW | escolher/criar na mão (ou quick mode) | criadas sozinhas |
| Cluster | ~17 passos de cliques | 1 comando |
| **Workload + HPA** | **sem botão — só `kubectl` no CloudShell** | mesmo comando já inclui |
| Tempo total | **30–45 min** (Parte 1) + terminal (Parte 2) | **~30 s de digitação** |
| Reproduzir/destruir | refazer tudo; destruir na ordem certa na mão | `eksctl create` / `delete` |
| Erro humano | altíssimo (role/subnet/YAML na mão) | quase nulo |

> 💡 É por isso que existe **eksctl** (e, no nível seguinte, **IaC**: CDK na
> Semana 6, que versiona essa infra como código).

---

## Exemplo 3 — 🟢 Budget de custo (barato)

### No Console (na mão)

1. Console → **Billing and Cost Management** → **Budgets**.
2. **Create budget** → **Customize (advanced)**.
3. **Budget type:** *Cost budget*.
4. **Name:** `cloudtask-mensal`.
5. **Period:** Monthly. **Amount:** ex. `10` USD.
6. **Configure thresholds:** alerta em 80% e 100%.
7. **Email recipients:** seu e-mail.
8. Revisar → **Create budget**.

**Tempo:** ~3–4 min, ~8 passos.

### Com a CLI (1 comando)

```bash
aws budgets create-budget --account-id <ACCOUNT_ID> \
  --budget '{"BudgetName":"cloudtask-mensal","BudgetLimit":{"Amount":"10","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST"}' \
  --notifications-with-subscribers '[{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN","Threshold":80},"Subscribers":[{"SubscriptionType":"EMAIL","Address":"voce@exemplo.com"}]}]'
```

### Veredito

| | Console | CLI |
| --- | --- | --- |
| Criar budget + alerta | ~8 passos, 3–4 min | 1 comando |
| Padronizar em N contas | refazer | script em loop |

---

## Exemplo 4 — O que o Console **nem consegue** fazer

Alguns passos da disciplina **não têm botão no console** — só existem via
`kubectl`/script:

- **Instalar o metrics-server** (pré-requisito do HPA): é um objeto Kubernetes,
  aplicado com `kubectl apply`/addon — não há "Create metrics-server" no console.
- **Criar o HPA**: `kubectl apply -f hpa.yaml`. O console do EKS mostra workloads,
  mas você não "desenha" um HPA clicando.
- **Aplicar Deployments/Services/Secrets**: tudo é YAML via `kubectl`/Kustomize.

> Lição: a partir do Kubernetes, **o mundo é declarativo (YAML + comando)**. O
> console serve para **olhar**, não para **construir** o dia a dia.

---

## Conclusão — por que automatizar

| Critério | Console (na mão) | Script / CLI / IaC |
| --- | --- | --- |
| **Velocidade** | minutos a dezenas de minutos | segundos |
| **Reprodutibilidade** | depende da memória/screenshot | idêntico sempre |
| **Versionável (git)** | não | sim (o comando/arquivo é texto) |
| **Revisável em equipe** | não | sim (pull request) |
| **Erro humano** | alto (campo/role/subnet errada) | baixo |
| **Destruir limpo** | na ordem certa, na mão | `delete` / `destroy` |
| **Bom para** | **aprender/inspecionar** 1 vez | **operar** de verdade |

**O que isso te mostra:** o console é ótimo para **entender** e **ver** o que
existe. Mas operar nuvem na mão **não escala** — é lento, erra fácil e não dá
para versionar. Por isso a disciplina evolui
**console → CLI → script → IaC (CDK, Semana 6)**.

---

## Próximos passos

| Quero... | Vá em |
| --- | --- |
| Ver os scripts que substituem isso | `scripts/build-and-push-ecr.sh`, `scripts/load-test-simple.py` |
| Fazer o HPA de verdade no app | [`14-hpa-carga-custos.md`](14-hpa-carga-custos.md) |
| DynamoDB pela app | [`15-eventos-dynamodb.md`](15-eventos-dynamodb.md) |
| Infra como código (próximo nível) | Semana 6 — CDK |
| Entender custos | [`../conceitos/cost-explorer.md`](../conceitos/cost-explorer.md) |
