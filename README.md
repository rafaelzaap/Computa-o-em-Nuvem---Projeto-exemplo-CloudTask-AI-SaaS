<!-- Área do Banner -->
<div align="center" style="background-color: white; max-width: 70%;">
  <img alt="BANNER do repositório CloudTask AI SaaS — disciplina Computação em Nuvem" title="Banner_CloudTask_AI_SaaS" src=".readme_docs/Banner_Github_NCPU.png" width="100%" />
</div>

<!-- Título e breve descrição do repositório -->
<div align="center">
  <h1>CloudTask AI SaaS — Aula 2</h1>
  <p><b>Branch <code>semana-01-fastapi-docker</code> — estado pós Aula 2.</b></p>
  <p>API FastAPI + Dockerfile multi-target + <b>Docker Compose</b> + devcontainer (agora consumindo o compose).</p>
</div>

<p align="center">
  <a href="https://www.python.org/" title="Python"><img src="https://github.com/get-icon/geticon/raw/master/icons/python.svg" alt="Python" height="21px"></a>
  +
  <a href="https://fastapi.tiangolo.com/" title="FastAPI"><img src="https://github.com/get-icon/geticon/raw/master/icons/fastapi.svg" alt="FastAPI" height="21px"></a>
  +
  <a href="https://www.docker.com/" title="Docker"><img src="https://github.com/get-icon/geticon/raw/master/icons/docker-icon.svg" alt="Docker" height="21px"></a>
</p>

## O que foi entregue nesta aula

- `docker-compose.yml` com o serviço `api` (target `dev` do Dockerfile, hot-reload, volume `.:/app`).
- `docker-compose.prod.yml` (override) simulando a imagem `prod` localmente.
- `.devcontainer/devcontainer.json` **migrado** de `build` direto para `dockerComposeFile` — o compose é agora a única fonte de verdade do ambiente.
- README atualizado.

> **Por que migrar o devcontainer para o compose já na Aula 2?**
> Na Aula 3 vamos adicionar o serviço `db` (PostgreSQL 16, compatível com Amazon RDS for PostgreSQL) ao mesmo compose. Com a migração feita agora, **nada muda** no `devcontainer.json` na Aula 3 — basta editar o compose, e o aluno ganha o banco automaticamente ao reabrir o devcontainer.

## O que continua igual (Aula 1)

- `app/main.py` + `app/api/routes_health.py` (endpoints `GET /` e `GET /health`).
- `app/schemas.py` (modelos Pydantic com exemplos para o Swagger).
- `Dockerfile` multi-target (`dev` / `prod`).
- `.dockerignore`, `requirements.txt`, `requirements-dev.txt`.
- `pyproject.toml` (ruff/pytest/mypy).
- `.vscode/launch.json` para debug.

## Pré-requisitos

| Ferramenta              | Versão mínima | Para quê                                         |
| ----------------------- | ------------- | ------------------------------------------------ |
| Git                     | 2.40          | Clonar e trocar de branches.                     |
| Docker Desktop          | 4.30          | Construir e rodar a imagem (compose v2 incluso). |
| VS Code                 | 1.90          | Editor de código.                                |
| Extensão Dev Containers | 0.380         | Abrir o projeto dentro do container.             |

## Como rodar

### 1) Devcontainer no VS Code (recomendado)

```text
1. Abra a pasta do repositório no VS Code.
2. F1 → "Dev Containers: Reopen in Container".
3. Aguarde o compose subir o serviço `api` (1ª vez ~1 min).
4. No terminal integrado:  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
5. Abra http://localhost:8000/docs no navegador do host.
```

### 2) Docker Compose direto (sem VS Code)

```bash
# dev (target dev, hot-reload, código montado)
docker compose up --build
# em background: docker compose up -d --build

# acompanhar logs
docker compose logs -f api

# parar
docker compose down

# simular produção
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### 3) Docker puro (também funciona)

```bash
docker build --target dev  -t cloudtask-api:dev  .
docker build --target prod -t cloudtask-api:prod .
docker run --rm -p 8000:8000 cloudtask-api:prod
```

## Endpoints

| Método | Caminho           | Descrição                                    |
| ------ | ----------------- | -------------------------------------------- |
| GET    | `/`               | Metadados da aplicação.                      |
| GET    | `/health`         | Liveness probe (`{"status": "ok"}`).         |
| GET    | `/docs`           | Swagger UI interativo (Markdown rico).       |
| GET    | `/redoc`          | ReDoc.                                       |
| GET    | `/openapi.json`   | Especificação OpenAPI.                       |

## Comandos úteis de Compose

```bash
docker compose ps                       # lista serviços rodando
docker compose exec api sh              # shell no container da API
docker compose logs -f api              # tail dos logs
docker compose build --no-cache api     # rebuild forçado
docker compose down -v                  # para tudo + remove volumes nomeados
```

## O que vem na próxima aula

- **Aula 3 (branch `semana-02-rds-vpc-seguranca`):**
  - Adicionar `postgres:16-alpine` como serviço `db` ao `docker-compose.yml` (compatível com Amazon RDS for PostgreSQL).
  - SQLAlchemy + Pydantic schemas + modelo `Task`.
  - CRUD completo de tarefas (`POST/GET/PUT/DELETE /tasks`).
  - Devcontainer **não muda** — só ganha o `db` automaticamente.

## Referências

- Issue da aula: [#2 — Aula 2](https://github.com/N-CPUninter/Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS/issues/2)
- Lista completa de tarefas: [`docs/TAREFAS.md`](docs/TAREFAS.md)
- Guia geral: [`docs/HOW_TO_USE.md`](docs/HOW_TO_USE.md)
- Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md)
- Exemplos didáticos: [`exemplos/dockerfile/`](exemplos/dockerfile/)

## Licença

[GNU General Public License v3.0](LICENSE).
