# Roadmap — CloudTask AI SaaS

Plano de evolução do projeto, **aula por aula**, ao longo de 6 semanas (12 aulas).
Cada aula tem uma branch `aula-XX-final` no GitHub contendo o estado acumulado.

---

## Convenções de versionamento

- **Branches:**
  - `main` — apenas guia, README e documentação geral. Só é atualizada ao final da disciplina (ou quando o professor decidir).
  - `semana-0X-tema` — branch principal de cada semana; acumula todo o código produzido naquela semana. Não é mergeada em `main`. A cada nova semana, a branch correspondente parte do estado da semana anterior.
  - `aula-XX-final` — estado pós-aula (o que será publicado e usado pelos alunos).
  - *(opcional)* `aula-XX-base` — estado pré-aula (ponto de partida).
  - *(opcional)* `aula-XX-desafio` — versão com lacunas para os alunos completarem.

  Branches de semana publicadas:
  - `semana-01-fastapi-docker`
  - `semana-02-rds-vpc-seguranca`
  - `semana-03-s3-kubernetes`
  - `semana-04-eks-aws`
  - `semana-05-custos-nosql-logs`
  - `semana-06-cdk-final`
- **Tags:**
  - `aula-01-start`, `aula-02-docker`, `aula-03-postgres-crud`, `aula-04-security-env`,
    `aula-05-s3-uploads`, `aula-06-kubernetes-local`, `aula-07-ecr`, `aula-08-eks`,
    `aula-09-scaling-costs`, `aula-10-dynamodb-logs`, `aula-11-cdk`, `aula-12-final`.

---

## Semana 1 — FastAPI + Docker

### Aula 1 — Início da API (`aula-01-final`)

**Entregas**
- Projeto FastAPI mínimo (`app/main.py`).
- Estrutura inicial de pastas.
- `requirements.txt`, `.gitignore`, `.env.example`, `README.md` atualizado.

**Endpoints**
```
GET /health
GET /
```

**Objetivo didático:** apresentar o que é uma API; preparar para Docker.

---

### Aula 2 — Docker (`aula-02-final`)

**Entregas**
- `Dockerfile`.
- `docker-compose.yml` rodando a API.
- README com instruções de build/run.

**Endpoints mantidos:** `GET /health`, `GET /`.

**Objetivo didático:** explicar containers, padronizar execução, preparar cloud-native.

---

## Semana 2 — PostgreSQL/RDS, VPC e Segurança

### Aula 3 — Banco SQL e CRUD (`aula-03-final`)

**Entregas**
- PostgreSQL no `docker-compose.yml`.
- SQLAlchemy + Pydantic schemas.
- Model `Task` (id, title, description, status, priority, created_at, updated_at).
- CRUD completo de tarefas.

**Endpoints**
```
POST   /tasks
GET    /tasks
GET    /tasks/{task_id}
PUT    /tasks/{task_id}
DELETE /tasks/{task_id}
```

**Objetivo didático:** persistência; banco SQL; preparação para RDS.

---

### Aula 4 — Segurança, variáveis e arquitetura cloud (`aula-04-final`)

**Entregas**
- `app/core/config.py` consumindo `.env`.
- Variáveis: `DATABASE_URL`, `APP_ENV`, `SECRET_KEY`.
- Documentação conceitual (sem provisionar AWS ainda):
  - `docs/aws-networking.md` — VPC, subnets pública/privada, SG, IG, bastion host.
  - `docs/security-model.md` — IAM, MFA, responsabilidade compartilhada, criptografia, LGPD.

**Objetivo didático:** código e infraestrutura pensados juntos; nada de credenciais em código.

---

## Semana 3 — S3, EFS, Data Lake e Kubernetes local

### Aula 5 — Uploads com S3 (`aula-05-final`)

**Entregas**
- Endpoint de upload + serviço `app/services/s3_service.py`.
- Modo local simulado (`STORAGE_MODE=local`) para alunos sem AWS.
- Pasta `local_uploads/` no `.gitignore`.
- Docs: `docs/s3-efs-datalake.md`.

**Endpoints**
```
POST /uploads
GET  /uploads/{filename}
```

**Variáveis**
```
STORAGE_MODE=local|s3
AWS_REGION=...
S3_BUCKET_NAME=...
```

**Objetivo didático:** arquivos fora do container; S3 como object storage e base de Data Lake.

---

### Aula 6 — Kubernetes local (`aula-06-final`)

**Entregas**
```
infra/k8s/
├── namespace.yaml
├── deployment.yaml
├── service.yaml
├── configmap.yaml
└── secret.example.yaml
```
- Kind ou Minikube.
- Deployment com múltiplas réplicas.

**Objetivo didático:** pods, deployment, service, replicas, auto healing — preparar EKS.

---

## Semana 4 — AWS Academy, ECR e EKS

### Aula 7 — ECR (`aula-07-final`)

**Entregas**
- `scripts/build-and-push-ecr.sh`.
- `docs/ecr-guide.md` (build, tag, push, AWS CLI, conceito de registry).

**Objetivo didático:** levar a imagem da máquina local para a cloud.

---

### Aula 8 — EKS (`aula-08-final`)

**Entregas**
```
infra/k8s/aws/
├── deployment-eks.yaml
├── service-loadbalancer.yaml
├── ingress-optional.yaml
└── README.md
```
- Imagem vindo do ECR.
- Service tipo `LoadBalancer`.

**Objetivo didático:** SaaS na AWS; Kubernetes gerenciado; alta disponibilidade.

---

## Semana 5 — Elasticidade, Cost Explorer, NoSQL leve e logs

### Aula 9 — Scaling e custos (`aula-09-final`)

**Entregas**
- `infra/k8s/hpa.yaml`.
- `scripts/load-test-simple.py`.
- Docs: `docs/cost-explorer.md`, `docs/aws-pricing-notes.md`.

**Objetivo didático:** elasticidade tem custo; introduzir billing.

---

### Aula 10 — DynamoDB / logs / eventos (`aula-10-final`)

**Entregas**
- `app/services/dynamodb_service.py`.
- Fallback local em JSON.
- Logs de criação/alteração de tarefas.

**Endpoints**
```
POST /events
GET  /events
```

**Evento:** `id`, `event_type`, `task_id`, `message`, `created_at`.

**Variáveis**
```
EVENT_STORE_MODE=local|dynamodb
DYNAMODB_TABLE_NAME=...
```

**Objetivo didático:** introduzir NoSQL sem aprofundar; uso comum p/ logs/eventos; ligação com Data Lake.

---

## Semana 6 — CDK, LGPD, backup e entrega final

### Aula 11 — AWS CDK (`aula-11-final`)

**Entregas**
```
infra/cdk/
├── app.py
├── requirements.txt
├── stacks/
│   ├── storage_stack.py   # S3
│   ├── ecr_stack.py
│   └── network_stack.py   # VPC básica opcional
└── README.md
```

**Objetivo didático:** introduzir IaC sem invadir o escopo de DevOps/Terraform.

---

### Aula 12 — Finalização (`aula-12-final`)

**Entregas**
```
docs/
├── final-report-template.md
├── lgpd-checklist.md
├── final-architecture.md
└── deployment-checklist.md
```
- README final completo.
- Arquitetura final consolidada.
- Checklists LGPD, segurança e custos.

**Objetivo didático:** preparar entrega final; consolidar SaaS completo; gerar relatório.

---

## Tabela-resumo

| Aula    | Branch           | Entrega-chave                              |
| ------- | ---------------- | ------------------------------------------ |
| Aula 1  | `aula-01-final`  | FastAPI mínimo com `/health`               |
| Aula 2  | `aula-02-final`  | Dockerfile e Docker Compose                |
| Aula 3  | `aula-03-final`  | PostgreSQL + CRUD de tarefas               |
| Aula 4  | `aula-04-final`  | `.env`, config, docs de VPC/IAM            |
| Aula 5  | `aula-05-final`  | Upload local/S3 + docs S3/EFS/Data Lake    |
| Aula 6  | `aula-06-final`  | Kubernetes local                           |
| Aula 7  | `aula-07-final`  | Build e push para ECR                      |
| Aula 8  | `aula-08-final`  | Deploy no EKS                              |
| Aula 9  | `aula-09-final`  | Scaling, HPA e custos                      |
| Aula 10 | `aula-10-final`  | Logs/eventos com DynamoDB ou JSON local    |
| Aula 11 | `aula-11-final`  | CDK básico                                 |
| Aula 12 | `aula-12-final`  | Documentação final + checklist de entrega  |

---

## Regras do projeto

- Cada etapa **funciona isoladamente** e é compatível com a anterior.
- Código **simples, didático, bem comentado**, adequado a alunos de ADS no meio do curso.
- Sempre que houver dependência AWS, **prover fallback local**.
- **Não usar Terraform** (CDK apenas na semana 6).
- **Não aprofundar CI/CD**.
- Sem Grafana / Prometheus.
- Sem autenticação complexa.
- Sem frontend avançado — **Swagger da FastAPI é a interface principal**.
- Foco: **Computação em Nuvem aplicada**.
