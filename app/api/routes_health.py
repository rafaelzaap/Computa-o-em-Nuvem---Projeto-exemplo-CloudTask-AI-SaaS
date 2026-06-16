"""Rotas de health-check da API CloudTask AI SaaS.

Endpoints leves usados por:

* ``HEALTHCHECK`` do Docker (definido no ``Dockerfile``).
* ``readinessProbe`` / ``livenessProbe`` do Kubernetes (Aulas 6 e 8).
* Load Balancers (ELB/ALB/NLB) na frente do EKS (Aula 8).

O ``/health`` não depende de banco nem de serviços externos — manter assim.
O ``/health/ready`` verifica conexão com PostgreSQL para readiness.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.database import SessionLocal
from app.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


HEALTH_DESCRIPTION = """\
Indica se o **processo da API está vivo**.

Endpoint leve e sem dependências externas, projetado para ser chamado por
orquestradores (Docker, Kubernetes, Load Balancers) **milhares de vezes
por dia** sem custo perceptível.

### Quando usar

| Consumidor | Configuração |
| --- | --- |
| Docker | `HEALTHCHECK` no `Dockerfile` |
| Kubernetes | `livenessProbe.httpGet.path: /health` |
| AWS ELB/ALB | Target Group Health Check Path = `/health` |

> <kbd>Importante</kbd> — esta rota **não** valida banco ou serviços
> externos. Para um check "está pronto para receber tráfego?", use
> `GET /health/ready`, que valida a conexão com PostgreSQL.

### Exemplos de uso

**curl**

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

**Python (httpx)**

```python
import httpx

resposta = httpx.get("http://localhost:8000/health")
assert resposta.status_code == 200
assert resposta.json() == {"status": "ok"}
```

**Manifest Kubernetes (trecho)**

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
```
"""


READY_DESCRIPTION = """\
Indica se a API está **pronta para receber tráfego**.

Este endpoint faz uma consulta mínima (`SELECT 1`) no PostgreSQL. Ele é mais
pesado que `/health`, então deve ser usado como **readiness probe**, não como
liveness probe.

### Por que separar?

| Endpoint | O que responde | Uso correto |
| --- | --- | --- |
| `/health` | Processo HTTP vivo | Reiniciar container travado |
| `/health/ready` | Banco respondendo | Enviar ou segurar tráfego |

Se o banco cair, o processo da API pode continuar vivo. Nesse caso `/health`
continua 200, mas `/health/ready` retorna 503 para avisar o orquestrador.
"""


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe da aplicação",
    description=HEALTH_DESCRIPTION,
    response_description="Estado do processo da API.",
    responses={
        200: {
            "description": "Aplicação viva e respondendo.",
            "content": {
                "application/json": {
                    "example": {"status": "ok"},
                }
            },
        },
    },
)
def health() -> HealthResponse:
    """Indica se o processo da API está vivo.

    Returns:
        HealthResponse: Objeto contendo ``status == "ok"`` quando o
        processo Python responde corretamente a requisições HTTP.

    Example:
        >>> health().status
        'ok'
    """
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe com PostgreSQL",
    description=READY_DESCRIPTION,
    response_description="Estado da prontidão da API.",
    responses={
        200: {
            "description": "Aplicação pronta para receber tráfego.",
            "content": {"application/json": {"example": {"status": "ready", "db": "ok"}}},
        },
        503: {
            "description": "Aplicação viva, mas ainda sem dependências críticas.",
            "content": {"application/json": {"example": {"status": "not_ready", "db": "down"}}},
        },
    },
)
def readiness() -> ReadyResponse | JSONResponse:
    """Check whether PostgreSQL is reachable."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadyResponse(status="not_ready", db="down").model_dump(),
        )

    return ReadyResponse(status="ready", db="ok")
