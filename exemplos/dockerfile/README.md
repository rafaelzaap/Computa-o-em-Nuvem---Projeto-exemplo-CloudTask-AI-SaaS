# Exemplos de Dockerfile

Três variantes do mesmo conceito — empacotar uma aplicação Python/FastAPI em uma imagem Docker — apresentadas em ordem crescente de sofisticação.

## Variantes

| Pasta            | O que mostra                                                                                     | Quando estudar          |
| ---------------- | ------------------------------------------------------------------------------------------------ | ----------------------- |
| [`01-minimo/`](01-minimo/)         | Dockerfile **mínimo absoluto** que funciona. 8 linhas, sem comentários, sem otimização.         | Primeiro contato.       |
| [`02-completo/`](02-completo/)     | Dockerfile **comentado linha a linha** com técnicas mais usadas: cache de dependências, usuário não-root, healthcheck, multi-stage. | Para entender cada recurso isoladamente. |
| [`03-cloudtask/`](03-cloudtask/)   | Dockerfile + `docker-compose.yml` + `.env.example` **prontos para o projeto CloudTask AI SaaS**, já com PostgreSQL no Compose. | Para copiar como base da Aula 2/3. |
| [`04-devcontainer-multi-target/`](04-devcontainer-multi-target/) | Dockerfile **multi-target** (`dev` / `test` / `prod`) + compose base+overrides + `.devcontainer/` do VS Code + workflow GitHub Actions + manifests para EKS. | A partir da Semana 4, para entrega final profissional. |

## Como rodar cada exemplo

Todos seguem o mesmo padrão. Entre na pasta da variante e use:

```bash
# build da imagem
docker build -t exemplo-fastapi .

# rodar
docker run --rm -p 8000:8000 exemplo-fastapi

# testar
curl http://localhost:8000/health
```

A variante `03-cloudtask` tem `docker-compose.yml` próprio (API + PostgreSQL):

```bash
cd 03-cloudtask
docker compose up --build
```

## Cada exemplo precisa de uma app mínima

Os exemplos `01-minimo` e `02-completo` esperam encontrar um arquivo `app/main.py` ao lado do `Dockerfile`. Use este snippet para teste:

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Exemplo")

@app.get("/")
def root():
    return {"hello": "world"}

@app.get("/health")
def health():
    return {"status": "ok"}
```

E um `requirements.txt`:

```text
fastapi
uvicorn[standard]
```

A variante `03-cloudtask` já traz o próprio `requirements.txt` e estrutura.

## Referências

- Documentação oficial Dockerfile: <https://docs.docker.com/engine/reference/builder/>
- Boas práticas: <https://docs.docker.com/develop/develop-images/dockerfile_best-practices/>
- Imagens base Python: <https://hub.docker.com/_/python>
