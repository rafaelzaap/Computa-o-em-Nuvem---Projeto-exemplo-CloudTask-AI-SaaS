<!-- Área do Banner -->
<div align="center" style="background-color: white; max-width: 70%;">
  <img alt="BANNER do repositório CloudTask AI SaaS — disciplina Computação em Nuvem" title="Banner_CloudTask_AI_SaaS" src=".readme_docs/Banner_Github_NCPU.png" width="100%" />
</div>

<!-- Título e breve descrição do repositório -->
<div align="center">
  <h1>CloudTask AI SaaS — Semana 2 (Aulas 3 e 4)</h1>
  <p><b>Base da Semana 1 evoluída com PostgreSQL, CRUD, configuração e segurança.</b></p>
  <p><b>FastAPI + Docker Compose + PostgreSQL</b>, com persistência via SQLAlchemy e settings por ambiente.</p>
</div>

<p align="center">
  <a href="https://www.python.org/" title="Python"><img src="https://github.com/get-icon/geticon/raw/master/icons/python.svg" alt="Python" height="21px"></a>
  +
  <a href="https://fastapi.tiangolo.com/" title="FastAPI"><img src="https://icon.icepanel.io/Technology/svg/FastAPI.svg" alt="FastAPI" height="21px"></a>
  +
  <a href="https://www.docker.com/" title="Docker"><img src="https://github.com/get-icon/geticon/raw/master/icons/docker-icon.svg" alt="Docker" height="21px"></a>
</p>

## O que foi feito nesta semana

Esta etapa parte da **Semana 1** e acrescenta a **Aula 3**. Abaixo, o que cada aula entregou.

### Aula 1 — Início da API (FastAPI mínimo)

- `app/main.py` — instância FastAPI + endpoint `GET /` (metadados).
- `app/api/routes_health.py` — endpoint `GET /health` (liveness).
- `app/schemas.py` — modelos Pydantic (`HealthResponse`, `RootResponse`) com exemplos no Swagger.
- `requirements.txt` (produção) e `requirements-dev.txt` (debug, lint, hot-reload).
- `Dockerfile` **multi-target** (`dev` / `prod`) com tini, usuário não-root e HEALTHCHECK.
- `.dockerignore`, `.devcontainer/devcontainer.json`, `.vscode/launch.json`.
- `pyproject.toml` (ruff / pytest / mypy).

### Aula 2 — Containerização com Docker Compose

- `docker-compose.yml` com o serviço `api` (target `dev` do Dockerfile, hot-reload, volume `.:/app`).
- `docker-compose.prod.yml` (override) simulando a imagem `prod` localmente.
- `.devcontainer/devcontainer.json` **migrado** de `build` direto para `dockerComposeFile` — o compose passa a ser a única fonte de verdade do ambiente.

### Aula 3 — PostgreSQL e CRUD de tarefas

- `docker-compose.yml` agora sobe também o serviço `db` com `postgres:16-alpine`.
- `app/db/database.py` cria engine, sessão por requisição e `Base` do SQLAlchemy.
- `app/db/models.py` define o modelo `Task`.
- `app/db/schemas.py` define os schemas Pydantic de entrada e saída.
- `app/api/routes_tasks.py` implementa CRUD completo em `/tasks`.

### Aula 4 — Configuração, segurança e readiness

- `app/core/config.py` centraliza variáveis de ambiente com `pydantic-settings`.
- `GET /health` continua sendo liveness puro, sem tocar no banco.
- `GET /health/ready` executa `SELECT 1` no PostgreSQL e retorna 503 se o banco cair.
- `TrustedHostMiddleware` lê `TRUSTED_HOSTS`.
- HSTS é aplicado apenas fora de desenvolvimento quando `FORCE_HTTPS=true`.
- Uvicorn sobe com `--proxy-headers`, preparado para ALB/Ingress no futuro.

> **Por que migrar o devcontainer para o compose já na Aula 2?**
> Na Aula 3 (Semana 2) adicionamos o serviço `db` (PostgreSQL 16, compatível com Amazon RDS) ao mesmo compose. Com a migração feita aqui, **nada muda** no `devcontainer.json` depois — basta editar o compose, e o aluno ganha o banco automaticamente ao reabrir o devcontainer.

Versão da API nesta etapa: **`0.2.0`**.

## Pré-requisitos

| Ferramenta              | Versão mínima | Para quê                                         |
| ----------------------- | ------------- | ------------------------------------------------ |
| Git                     | 2.40          | Clonar e trocar de branches.                     |
| Docker Desktop          | 4.30          | Construir e rodar a imagem (compose v2 incluso). |
| VS Code                 | 1.90          | Editor de código.                                |
| Extensão Dev Containers | 0.380         | Abrir o projeto dentro do container.             |

## Como rodar

> ⚠️ **Ao mudar de semana (branch), faça REBUILD do devcontainer.**
> A imagem do container é um snapshot congelado das dependências da branch em
> que foi construída. Cada semana acrescenta libs novas em `requirements.txt`.
> Sem rebuild, o `uvicorn` quebra com `ModuleNotFoundError` ao importar uma lib
> que ainda não foi instalada e o Swagger sai do ar.
>
> No VS Code: `F1` → **Dev Containers: Rebuild and Reopen in Container**.
>
> Para saber se precisa rebuild antes de trocar de branch:
> ```bash
> git diff <branch-atual> <branch-destino> -- requirements.txt requirements-dev.txt requirements-test.txt Dockerfile docker-compose.yml
> ```
> Se mostrar diff → rebuild. Entre **aulas da mesma semana**, geralmente
> código apenas — não precisa rebuild.

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
| GET    | `/health/ready`   | Readiness probe com consulta ao PostgreSQL.  |
| POST   | `/tasks`          | Cria uma tarefa.                             |
| GET    | `/tasks`          | Lista tarefas.                               |
| GET    | `/tasks/{id}`     | Busca uma tarefa.                            |
| PUT    | `/tasks/{id}`     | Atualiza uma tarefa.                         |
| DELETE | `/tasks/{id}`     | Remove uma tarefa.                           |
| GET    | `/docs`           | Swagger UI interativo (Markdown rico).       |
| GET    | `/redoc`          | ReDoc.                                       |
| GET    | `/openapi.json`   | Especificação OpenAPI.                       |

## Comandos úteis de Compose

```bash
docker compose ps                       # lista serviços rodando
docker compose exec api sh              # shell no container da API
docker compose exec db psql -U cloudtask -d cloudtask
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
- **Configuração do zero (terminal, Docker, AWS CLI, Learner Lab):** [`docs/praticas/00-setup-inicial-e-aws-academy.md`](docs/praticas/00-setup-inicial-e-aws-academy.md)
- Exemplos didáticos: [`exemplos/dockerfile/`](exemplos/dockerfile/)

## Licença

[GNU General Public License v3.0](LICENSE).
