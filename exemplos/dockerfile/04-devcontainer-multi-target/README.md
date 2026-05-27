# Dockerfile multi-target + devcontainer + CI + EKS

Versão avançada do exemplo `03-cloudtask`. Mostra como **um único Dockerfile** gera três imagens diferentes via `--target`, e como cada uma é usada num momento diferente do ciclo de vida:

| Target | Onde é usada                                   | Contém                                          |
| ------ | ---------------------------------------------- | ----------------------------------------------- |
| `dev`  | Devcontainer do VS Code / `docker-compose.dev` | Libs de prod + test + dev (debugpy, ipdb, ruff) |
| `test` | CI no GitHub Actions / `docker-compose.test`   | Libs de prod + test, código e `tests/` embutidos |
| `prod` | Push para ECR → deploy no EKS                  | **Só** o necessário em runtime. Sem teste/dev.  |

## Estrutura da pasta

```text
04-devcontainer-multi-target/
├── Dockerfile                       # multi-target (dev, test, prod)
├── .dockerignore
├── .env.example
├── requirements.txt                 # prod
├── requirements-test.txt            # adicional para test
├── requirements-dev.txt             # adicional para dev
├── docker-compose.yml               # base (comum aos 3 ambientes)
├── docker-compose.dev.yml           # override DEV
├── docker-compose.test.yml          # override TEST
├── docker-compose.prod.yml          # override PROD (smoke test local)
├── .devcontainer/
│   └── devcontainer.json            # VS Code Dev Containers
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions (apenas didático)
└── k8s/
    ├── namespace.yaml
    ├── deployment.yaml              # consome a imagem prod do ECR
    ├── service.yaml                 # LoadBalancer no EKS
    └── secret.example.yaml          # modelo de Secret (não commite o real)
```

## Como o aluno usa cada ambiente

### Desenvolvimento (VS Code devcontainer)

1. Instale a extensão **Dev Containers** (`ms-vscode-remote.remote-containers`).
2. Abra esta pasta no VS Code.
3. `F1` → **Dev Containers: Reopen in Container**.

O VS Code constrói a imagem no target `dev`, sobe junto o PostgreSQL e anexa o editor ao container `api`. Hot-reload do `uvicorn` ativo; debug remoto na porta `5678` (`debugpy`).

### Desenvolvimento (sem VS Code)

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Testes locais (imitando o CI)

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api
```

### Smoke test "tipo produção"

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### CI (GitHub Actions)

O arquivo `.github/workflows/ci.yml` deste exemplo **não é ativo** (está dentro de `exemplos/`, GitHub só lê na raiz). Para usar em um projeto real, copie para `.github/workflows/ci.yml` na raiz do repo.

O workflow:

1. **Job `tests`** — em todo push/PR: constrói o target `test` e roda `pytest` com PostgreSQL temporário.
2. **Job `build-and-push`** — só em push para `main` e após testes passarem: constrói o target `prod` e empurra para o **Amazon ECR** com tags `latest` e SHA do commit.

Secrets necessários no repositório GitHub:

| Secret                       | Para quê                                                           |
| ---------------------------- | ------------------------------------------------------------------ |
| `AWS_GITHUB_OIDC_ROLE_ARN`   | Role na AWS que o GitHub Actions assume via OIDC (recomendado).    |

> Alternativa mais simples (menos segura): use `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` como secrets e troque o step `configure-aws-credentials`.

### Deploy no EKS

Depois do CI ter publicado a imagem `prod` no ECR:

```bash
# 1) editar k8s/deployment.yaml e substituir <ACCOUNT_ID> e <REGION>
# 2) criar o secret real (NÃO use o exemplo)
kubectl create secret generic cloudtask-secrets -n cloudtask \
  --from-literal=DATABASE_URL='...' \
  --from-literal=SECRET_KEY='...'

# 3) aplicar
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 4) descobrir IP público
kubectl get svc -n cloudtask cloudtask-api
```

## Por que separar targets?

- **Segurança em prod**: a imagem do EKS não tem `pytest`, `ruff`, `debugpy` nem código de teste. Menor superfície de ataque, menor tamanho, menor custo de pull.
- **Build cache eficiente**: alterar um arquivo de teste não invalida a camada de produção.
- **Mesmo Dockerfile**: garante que dev, test e prod compartilham 100% da base (Python, libpq, usuário, env vars). Sem "funciona na minha máquina".

## Diagrama do fluxo

```text
                +-------------+
  desenvolve →  | target: dev | → devcontainer + hot-reload + debug remoto
                +-------------+

                +-------------+
   git push  →  | target: test| → GitHub Actions → pytest passa?
                +-------------+

                +-------------+
   passou    →  | target: prod| → push ECR → kubectl apply → EKS → usuário
                +-------------+
```

## Quando NÃO usar este modelo

- Projeto-pet de poucas horas: use o `01-minimo` ou `03-cloudtask`.
- Sem PostgreSQL nem CI: complexidade desnecessária.

Para projetos da disciplina a partir da **Semana 4** (já com ECR + EKS), este é um bom ponto de partida para a entrega final.
