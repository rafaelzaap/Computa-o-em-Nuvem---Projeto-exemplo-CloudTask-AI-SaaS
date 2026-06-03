# Prática 10 — Deploy semana-02 no Fargate com Postgres em container

> **Objetivo didático:** subir a aplicação da **Semana 2** (FastAPI + Postgres)
> 100% em containers no **ECS Fargate**, com o banco de dados rodando como um
> **container ao lado da API** (sem RDS, sem volume persistente). O ponto da
> aula é **demonstrar na pele** o problema disso: ao reiniciar a task, os
> dados somem.
>
> No caminho ensinamos:
> 1. **Configurar `.env` na AWS via Secrets Manager** (sem deixar senha em
>    texto puro).
> 2. **Linkar o repositório GitHub à AWS via CodeBuild** (build automatizado).
> 3. **Provar empiricamente** por que produção usa RDS.
>
> **Quando:** Semana 2 (opcional, depois do código local rodar). Quem quiser
> a versão "produção real" com RDS vai direto para a
> [`09-deploy-manual-aws.md`](09-deploy-manual-aws.md) (Aulas 7+).
>
> **Tempo:** 60–90 min (primeiro deploy). 30 min nas próximas iterações.
> **Custo Learner Lab:** ~$0,50 em 2 h (Fargate + ELB opcional). **Limpe!**
>
> **Pré-req:**
> - Devcontainer da semana-02 rodando.
> - AWS CLI funcionando: `aws sts get-caller-identity` retorna seu ARN.
> - Conceitos: [`../conceitos/infra-aws-minima-por-semana.md`](../conceitos/infra-aws-minima-por-semana.md)
>   (seção "Postgres: container vs RDS") e
>   [`../conceitos/security-model.md`](../conceitos/security-model.md).

---

## 1. Por que essa prática é didática (e arriscada na vida real)

Em produção ninguém roda Postgres como container ECS sem volume porque:

| Risco | O que acontece |
| --- | --- |
| **Perda de dados** | Fargate **não tem disco local persistente**. Se a task reiniciar (deploy novo, OOM, scheduler, AZ down) o container do banco vem **vazio**. |
| **Sem backup automático** | Ninguém faz backup pra você. Acidente = recriação manual. |
| **Sem Multi-AZ** | Task vive em uma AZ. AZ cai → API e banco caem juntos. |
| **Sem ponto de restauração** | Sem snapshot. "Voltar 1 hora" não é opção. |
| **Migrações ficam frágeis** | Cada restart roda `create_all` de novo; sem Alembic você nem versiona schema. |
| **Cobrança de IOPS escondida** | Fargate cobra por minuto ligado mesmo se o banco estiver ocioso. |

**O exercício é exatamente para você sentir isso.** Vamos:

1. Subir.
2. Criar tarefas via API.
3. Forçar restart da task.
4. Constatar: **dados sumiram**.
5. Concluir: produção precisa de RDS (Aula 7+).

---

## 2. Visão geral da arquitetura

```text
        usuário
           │ HTTP :8000
           ▼
   ┌──────────────────────────────────────────┐
   │      ECS Fargate Task (1 task)           │
   │                                          │
   │  ┌──────────────┐    ┌────────────────┐  │
   │  │ Container    │    │ Container      │  │
   │  │ api          │◄──►│ db (postgres)  │  │
   │  │ uvicorn:8000 │    │ :5432          │  │
   │  └──────────────┘    └────────────────┘  │
   │   localhost:5432 (mesma task = mesma loopback)
   │                                          │
   │   secrets/env vars injetados via         │
   │   AWS Secrets Manager + ECS              │
   └──────────────────────────────────────────┘
              │
              │ Public IP (didático) ou ALB (mais real)
              ▼
          0.0.0.0:8000 → 8000 do container api
```

**Decisão-chave:** **2 containers na MESMA task definition**. Vantagem: comunicam por `localhost:5432`. Desvantagem: caem juntos.

Alternativa (mais complexa, fora desta prática): 2 tasks/services separados + AWS Cloud Map (service discovery). Mesma fragilidade de dados, mais setup.

---

## 3. Subir o `.env` da aplicação para o AWS Secrets Manager

> **POR QUÊ:** nunca deixar senha em texto puro na task definition. Secrets
> Manager dá um cofre, criptografado por KMS, com IAM controlando quem lê.

### 3.1. Decidir os valores

```bash
# Gerar senha forte do Postgres (no terminal do devcontainer)
export PG_PASSWORD="$(openssl rand -hex 16)"
echo "PG_PASSWORD=$PG_PASSWORD"  # anote, vamos usar abaixo

# Gerar SECRET_KEY da aplicação
export SECRET_KEY="$(openssl rand -hex 32)"
echo "SECRET_KEY=$SECRET_KEY"
```

### 3.2. Criar o secret

```bash
aws secretsmanager create-secret \
  --name cloudtask/semana02/dev \
  --description "Env da semana-02 rodando no Fargate" \
  --secret-string "{
    \"POSTGRES_USER\":\"cloudtask\",
    \"POSTGRES_PASSWORD\":\"$PG_PASSWORD\",
    \"POSTGRES_DB\":\"cloudtask\",
    \"DATABASE_URL\":\"postgresql://cloudtask:$PG_PASSWORD@localhost:5432/cloudtask\",
    \"SECRET_KEY\":\"$SECRET_KEY\",
    \"APP_ENV\":\"production\",
    \"LOG_LEVEL\":\"INFO\"
  }"
```

> 💡 `localhost:5432` funciona porque os 2 containers compartilham a **mesma
> rede** dentro da task Fargate.

### 3.3. Capturar o ARN do secret

```bash
export SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id cloudtask/semana02/dev \
  --query ARN --output text)
echo "SECRET_ARN=$SECRET_ARN"
```

Guarde — vamos referenciar este ARN na task definition.

> ⚠️ **Learner Lab limitação:** algumas contas Learner Lab restringem
> `kms:Decrypt` para keys customizadas. O secret default usa a key gerenciada
> da AWS (`aws/secretsmanager`) — geralmente funciona. Se der erro de KMS no
> step 8, veja o troubleshooting.

---

## 4. Conectar o repositório GitHub à AWS (CodeBuild)

> **Opcional**, mas didático: em vez de buildar a imagem no seu devcontainer,
> deixe a **AWS** buildar a partir do GitHub. Simula um pipeline real.

> Quem quiser pular e buildar localmente: vá pro **§5**.

### 4.1. Criar Personal Access Token (PAT) do GitHub

1. GitHub → Settings → Developer Settings → Personal Access Tokens →
   Tokens (classic).
2. Permissões mínimas:
   - `repo` (público + privado: leitura completa).
3. Copie o token (`ghp_...`). **Você só vê uma vez.**

### 4.2. Importar o token no CodeBuild (uma vez por conta)

```bash
aws codebuild import-source-credentials \
  --server-type GITHUB \
  --auth-type PERSONAL_ACCESS_TOKEN \
  --token "ghp_SEU_TOKEN_AQUI"
```

### 4.3. Criar `buildspec.yml` na raiz do repo

```yaml
# buildspec.yml — usado pelo CodeBuild
version: 0.2
phases:
  pre_build:
    commands:
      - echo "Login no ECR..."
      - aws ecr get-login-password --region $AWS_REGION \
          | docker login --username AWS --password-stdin $ECR_REPO_URI
      - IMAGE_TAG=v$(date +%Y%m%d-%H%M%S)
      - echo "IMAGE_TAG=$IMAGE_TAG"
  build:
    commands:
      - echo "Build da imagem cloudtask-api target prod..."
      - docker build --target prod -t cloudtask-api:$IMAGE_TAG .
      - docker tag cloudtask-api:$IMAGE_TAG $ECR_REPO_URI:$IMAGE_TAG
      - docker tag cloudtask-api:$IMAGE_TAG $ECR_REPO_URI:latest
  post_build:
    commands:
      - echo "Push para ECR..."
      - docker push $ECR_REPO_URI:$IMAGE_TAG
      - docker push $ECR_REPO_URI:latest
      - echo "Done. Tag final = $IMAGE_TAG"
```

Commit + push para o branch `semana-02-rds-vpc-seguranca`.

### 4.4. Criar o projeto CodeBuild no Console

Learner Lab bloqueia parte da criação via CLI; faça pelo Console:

1. Console → CodeBuild → Create build project.
2. **Project name:** `cloudtask-semana02-build`.
3. **Source:** GitHub → seu repo → branch
   `semana-02-rds-vpc-seguranca`.
4. **Environment:**
   - Managed image, Ubuntu, Standard 7.0.
   - **Privileged: ON** (necessário para `docker build`).
   - Service role: **LabRole** (única disponível no Learner Lab).
5. **Buildspec:** Use the `buildspec.yml`.
6. **Environment variables:**
   - `AWS_REGION` = `us-east-1`
   - `ECR_REPO_URI` = preencher depois de criar o repo no §5.
7. Create build project. (NÃO clique Start build ainda — espera o ECR.)

> 💡 Sem CodeBuild também funciona — siga o §5 fazendo `docker build` + `docker push` do seu devcontainer.

---

## 5. Criar o repositório ECR

```bash
aws ecr create-repository \
  --repository-name cloudtask-semana02 \
  --region us-east-1

export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO_URI=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cloudtask-semana02
echo "ECR_REPO_URI=$ECR_REPO_URI"
```

Se você criou o projeto CodeBuild no §4, volte lá e preencha
`ECR_REPO_URI` na env var.

### 5.1. Build + push (sem CodeBuild — caminho rápido)

```bash
# Login no ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin $ECR_REPO_URI

# Build do target prod
docker build --target prod -t cloudtask-semana02:v1 .

# Tag e push
docker tag cloudtask-semana02:v1 $ECR_REPO_URI:v1
docker tag cloudtask-semana02:v1 $ECR_REPO_URI:latest
docker push $ECR_REPO_URI:v1
docker push $ECR_REPO_URI:latest

# Conferir
aws ecr list-images --repository-name cloudtask-semana02
```

### 5.2. Build + push (via CodeBuild)

No Console do projeto criado no §4: **Start build**. Acompanhe os logs.
Quando terminar, confira:

```bash
aws ecr describe-images --repository-name cloudtask-semana02
```

---

## 6. Criar cluster ECS Fargate

```bash
aws ecs create-cluster --cluster-name cloudtask-fargate
```

> 💡 Cluster Fargate não cobra para existir; só pelas tasks que rodam.

---

## 7. Task Definition: 2 containers (api + db)

> Aqui mora a magia da prática. **API e Postgres no mesmo task** =
> compartilham loopback. Sem volume persistente = perda de dados no restart.

### 7.1. Criar arquivo de task definition

Salve como `infra/aws/task-def-semana02.json` (vamos versionar no repo
para o aluno comparar mudanças no futuro):

```json
{
  "family": "cloudtask-semana02",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/LabRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/LabRole",

  "containerDefinitions": [
    {
      "name": "db",
      "image": "postgres:16-alpine",
      "essential": true,
      "portMappings": [
        { "containerPort": 5432, "protocol": "tcp" }
      ],
      "secrets": [
        { "name": "POSTGRES_USER",     "valueFrom": "SECRET_ARN:POSTGRES_USER::" },
        { "name": "POSTGRES_PASSWORD", "valueFrom": "SECRET_ARN:POSTGRES_PASSWORD::" },
        { "name": "POSTGRES_DB",       "valueFrom": "SECRET_ARN:POSTGRES_DB::" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cloudtask-semana02",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "db",
          "awslogs-create-group": "true"
        }
      }
    },
    {
      "name": "api",
      "image": "ECR_REPO_URI:latest",
      "essential": true,
      "dependsOn": [
        { "containerName": "db", "condition": "START" }
      ],
      "portMappings": [
        { "containerPort": 8000, "protocol": "tcp" }
      ],
      "secrets": [
        { "name": "DATABASE_URL", "valueFrom": "SECRET_ARN:DATABASE_URL::" },
        { "name": "SECRET_KEY",   "valueFrom": "SECRET_ARN:SECRET_KEY::"   },
        { "name": "APP_ENV",      "valueFrom": "SECRET_ARN:APP_ENV::"      },
        { "name": "LOG_LEVEL",    "valueFrom": "SECRET_ARN:LOG_LEVEL::"    }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cloudtask-semana02",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
```

### 7.2. Substituir placeholders e registrar

```bash
mkdir -p infra/aws

# Gera o JSON final substituindo ACCOUNT_ID, ECR_REPO_URI e SECRET_ARN
sed -e "s|ACCOUNT_ID|$ACCOUNT_ID|g" \
    -e "s|ECR_REPO_URI|$ECR_REPO_URI|g" \
    -e "s|SECRET_ARN|$SECRET_ARN|g" \
    infra/aws/task-def-semana02.json > /tmp/task-def-resolved.json

# Registra na AWS
aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-def-resolved.json
```

> 💡 **Sintaxe `SECRET_ARN:CHAVE::`** no `valueFrom`: ECS faz lookup do
> secret e extrai a chave do JSON automaticamente. Sem essa sintaxe ele
> jogaria o JSON inteiro na env var.

---

## 8. Criar Security Group + Service

### 8.1. SG permitindo 8000 público

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true \
  --query "Vpcs[0].VpcId" --output text)

aws ec2 create-security-group \
  --group-name cloudtask-semana02-sg \
  --description "Allow 8000 from anywhere (didactic)" \
  --vpc-id $VPC_ID

export SG_ID=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=cloudtask-semana02-sg \
  --query "SecurityGroups[0].GroupId" --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

> ⚠️ `0.0.0.0/0` é **inseguro em produção**. Aqui é didático: só pra você
> acessar do seu laptop. Em produção: ALB ou range restrito.

### 8.2. Capturar subnets públicas

```bash
export SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" \
  --query "Subnets[].SubnetId" --output text | tr '\t' ',')
echo "SUBNETS=$SUBNETS"
```

### 8.3. Criar Service Fargate (1 task, Public IP)

```bash
aws ecs create-service \
  --cluster cloudtask-fargate \
  --service-name cloudtask-semana02 \
  --task-definition cloudtask-semana02 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"
```

### 8.4. Aguardar task ficar `RUNNING`

```bash
aws ecs wait services-stable \
  --cluster cloudtask-fargate \
  --services cloudtask-semana02

# pegar Public IP
export TASK_ARN=$(aws ecs list-tasks \
  --cluster cloudtask-fargate \
  --service-name cloudtask-semana02 \
  --query "taskArns[0]" --output text)

export ENI_ID=$(aws ecs describe-tasks \
  --cluster cloudtask-fargate --tasks $TASK_ARN \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" \
  --output text)

export PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI_ID \
  --query "NetworkInterfaces[0].Association.PublicIp" --output text)

echo "API publicada em http://$PUBLIC_IP:8000"
```

### 8.5. Testar

```bash
curl http://$PUBLIC_IP:8000/health
# {"status":"ok"}

curl http://$PUBLIC_IP:8000/health/ready
# {"status":"ok","database":"ok"}

# Abrir o Swagger no navegador
echo "http://$PUBLIC_IP:8000/docs"
```

---

## 9. **A demonstração dolorosa:** perda de dados

### 9.1. Criar dados via API

```bash
for i in 1 2 3 4 5; do
  curl -sX POST http://$PUBLIC_IP:8000/tasks \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Tarefa Fargate #$i\",\"priority\":\"high\"}"
  echo
done

curl -s http://$PUBLIC_IP:8000/tasks | jq 'length'
# 5
```

### 9.2. Forçar restart da task

```bash
aws ecs stop-task \
  --cluster cloudtask-fargate \
  --task $TASK_ARN \
  --reason "demonstrando perda de dados em container DB sem volume"
```

ECS automaticamente sobe nova task (desired-count=1). Aguarde:

```bash
aws ecs wait services-stable \
  --cluster cloudtask-fargate \
  --services cloudtask-semana02

# Capturar o NOVO IP (task nova = IP novo)
export TASK_ARN=$(aws ecs list-tasks --cluster cloudtask-fargate \
  --service-name cloudtask-semana02 --query "taskArns[0]" --output text)
export ENI_ID=$(aws ecs describe-tasks --cluster cloudtask-fargate \
  --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" --output text)
export PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI_ID --query "NetworkInterfaces[0].Association.PublicIp" --output text)
echo "Novo IP: $PUBLIC_IP"
```

### 9.3. Conferir os dados

```bash
curl -s http://$PUBLIC_IP:8000/tasks | jq
# []
```

> 🎯 **DEMONSTRADO.** 5 tarefas perdidas. Schema também: foi recriado pelo
> `create_all` no startup, mas dados não voltam.

**Discussão em sala:**

- Em produção isso significaria clientes perdendo trabalho.
- Recuperação? Nenhuma — não há snapshot.
- Mesmo com `desired-count > 1`, dados não replicam entre instâncias.
- **Saída:** RDS (Aula 7+), com snapshots automáticos e Multi-AZ.

> 💡 Quer mitigação parcial? Use **EFS** como volume montado em
> `/var/lib/postgresql/data`. Solução desaconselhada — Postgres em EFS tem
> performance ruim e race conditions com fsync. **Use RDS.** É o motivo de
> existir.

---

## 10. Cleanup obrigatório

```bash
# Service para 0 tasks
aws ecs update-service \
  --cluster cloudtask-fargate \
  --service cloudtask-semana02 \
  --desired-count 0

aws ecs delete-service \
  --cluster cloudtask-fargate \
  --service cloudtask-semana02 \
  --force

# Cluster
aws ecs delete-cluster --cluster cloudtask-fargate

# Security Group (esperar service derrubar antes)
aws ec2 delete-security-group --group-id $SG_ID

# Secret
aws secretsmanager delete-secret \
  --secret-id cloudtask/semana02/dev \
  --force-delete-without-recovery

# ECR repo
aws ecr delete-repository \
  --repository-name cloudtask-semana02 \
  --force

# CloudWatch log group
aws logs delete-log-group --log-group-name /ecs/cloudtask-semana02

# CodeBuild project (se criou)
aws codebuild delete-project --name cloudtask-semana02-build

# Confirmar
aws ecs list-clusters
aws ecr describe-repositories 2>/dev/null
aws secretsmanager list-secrets --filters Key=name,Values=cloudtask
```

> ⚠️ Confira o **Cost Explorer** em 24 h. Qualquer custo residual aponta o
> que escapou.

---

## 11. Troubleshooting

| Erro | Causa | Fix |
| --- | --- | --- |
| `ResourceInitializationError: unable to pull secrets` | LabRole sem permissão `secretsmanager:GetSecretValue` ou KMS | Confirme o ARN do secret; use a key default `aws/secretsmanager` |
| Task fica em `PROVISIONING` minutos | subnets sem rota pra internet | use **subnets públicas** com `assignPublicIp=ENABLED` |
| `db` container reinicia em loop | imagem `postgres:16-alpine` espera env vars | confirme que o secret tem POSTGRES_USER/PASSWORD/DB e está injetando |
| API `502` ou conexão recusada | `db` ainda subindo | `dependsOn` com `condition: START` ajuda, mas pode precisar de retry no app |
| `400 Bad Request` ao registrar task def | JSON inválido após sed | abra `/tmp/task-def-resolved.json` e valide com `jq .` |
| ECR `denied: User: ... is not authorized` | login expirou | rode novamente `aws ecr get-login-password ... \| docker login ...` |
| CodeBuild falha em `docker build` | sem `privileged: true` | edite o projeto e marque "Privileged" |

---

## 12. Próximos passos

| Quero... | Vá em |
| --- | --- |
| Versão "produção" com RDS | [`09-deploy-manual-aws.md`](09-deploy-manual-aws.md) §7 |
| Comparar Fargate × EKS | [`../conceitos/infra-aws-minima-por-semana.md`](../conceitos/infra-aws-minima-por-semana.md) §7 |
| HTTPS na frente | [`../conceitos/https-tls.md`](../conceitos/https-tls.md) |
| Modelo de segurança / Secrets | [`../conceitos/security-model.md`](../conceitos/security-model.md) |
| Resolver erros AWS gerais | [`99-troubleshooting.md`](99-troubleshooting.md) |
