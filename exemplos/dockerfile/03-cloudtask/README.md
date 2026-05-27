# Dockerfile e Docker Compose — CloudTask AI SaaS

Versão **pronta para uso** na disciplina, ajustada para a estrutura real do projeto. Use como ponto de partida das aulas 2 e 3.

## Arquivos

| Arquivo               | Para que serve                                                          |
| --------------------- | ----------------------------------------------------------------------- |
| `Dockerfile`          | Empacota a aplicação FastAPI (multi-stage, usuário não-root, healthcheck). |
| `docker-compose.yml`  | Sobe **API + PostgreSQL** em containers, prontos para o CRUD.           |
| `.env.example`        | Variáveis de ambiente esperadas pelo Compose. Copie para `.env`.        |
| `.dockerignore`       | Evita levar pastas grandes (docs, exemplos, infra, etc.) na imagem.     |

## Pré-requisitos

- Docker Desktop 4.30+
- Docker Compose v2 (`docker compose version`)
- Código mínimo do CloudTask AI SaaS na raiz do repositório (esperado: `app/main.py`, `requirements.txt`).

## Como rodar

A partir desta pasta (`exemplos/dockerfile/03-cloudtask/`):

```bash
# 1) prepare o .env
cp .env.example .env

# 2) suba tudo
docker compose up --build

# 3) em outro terminal, teste
curl http://localhost:8000/health
# resposta esperada: {"status":"ok"}
```

A primeira execução baixa as imagens e constrói a sua. Próximas subidas são bem mais rápidas (cache).

## Estrutura assumida

O `docker-compose.yml` faz `build` apontando para a **raiz do projeto** (três níveis acima desta pasta), por isso espera encontrar lá:

```text
cloudtask-ai-saas/
├── app/
│   └── main.py             # FastAPI ("app")
├── requirements.txt
└── exemplos/
    └── dockerfile/
        └── 03-cloudtask/
            ├── Dockerfile
            ├── docker-compose.yml
            ├── .dockerignore
            └── .env.example
```

Se a sua aplicação ainda não tem `app/main.py`, copie o snippet mínimo do [`README` da pasta `dockerfile/`](../README.md).

## O que este exemplo demonstra

- **Compose com 2 serviços** (`api` + `db`) e `depends_on` com healthcheck.
- **Volume nomeado** (`pgdata`) garantindo persistência do banco entre `docker compose down` e `up`.
- **Hot-reload em dev** via `volumes: ../../../app:/app/app:ro` — alterações no código aparecem sem rebuild.
- **`env_file`** centralizando configuração.
- **Variáveis com default** (`${APP_PORT:-8000}`) para o caso de o `.env` faltar.

## Comandos úteis

```bash
docker compose ps                       # lista serviços
docker compose logs -f api              # tail dos logs da API
docker compose exec api sh              # shell dentro do container da API
docker compose exec db psql -U cloudtask cloudtask  # cliente psql
docker compose down                     # para tudo (mantém o volume)
docker compose down -v                  # para tudo + ZERA o banco
```

## Como adaptar para a sua aula

1. Mova o `Dockerfile` deste exemplo para a **raiz do seu projeto**.
2. Mova o `docker-compose.yml` também, ajustando `context: .` e o caminho do `dockerfile`.
3. Ajuste o `.dockerignore` à sua estrutura.
4. Versione **apenas** o `Dockerfile`, `docker-compose.yml`, `.dockerignore` e `.env.example` — nunca o `.env`.
