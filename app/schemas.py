"""
Schemas Pydantic compartilhados por toda a aplicação.

Modelos definidos aqui são usados como ``response_model`` nas rotas
FastAPI; os ``examples`` declarados via :class:`pydantic.Field` aparecem
automaticamente no Swagger (``GET /docs``), permitindo que o usuário
clique em **Try it out** e veja a estrutura esperada.

Em aulas futuras criaremos schemas específicos em ``app/db/schemas.py``
para os modelos do banco (Task, Event, etc.). Por enquanto, este módulo
concentra apenas os schemas de uso geral (health, root).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Resposta padrão do endpoint :func:`app.api.routes_health.health`.

    Atributos:
        status: Sempre ``"ok"`` quando o processo da API está vivo.
            Em aulas futuras (Aula 3+) criaremos um ``/health/ready`` que
            poderá retornar outros valores quando o banco estiver fora.

    Example:
        >>> HealthResponse(status="ok").model_dump()
        {'status': 'ok'}
    """

    status: Literal["ok"] = Field(
        default="ok",
        description="Estado da aplicação. `ok` indica que o processo está vivo.",
        examples=["ok"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ok"},
            ]
        }
    )


class ReadyResponse(BaseModel):
    """Resposta do endpoint de readiness da aplicação."""

    status: Literal["ready", "not_ready"] = Field(
        ...,
        description="`ready` indica que dependências críticas responderam.",
        examples=["ready"],
    )
    db: Literal["ok", "down"] = Field(
        ...,
        description="Estado da conexão com PostgreSQL.",
        examples=["ok"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ready", "db": "ok"},
                {"status": "not_ready", "db": "down"},
            ]
        }
    )


class RootResponse(BaseModel):
    """Resposta do endpoint raiz :func:`app.main.root`.

    Devolve metadados básicos da aplicação para que clientes (humanos ou
    máquinas) identifiquem o serviço e encontrem rapidamente a documentação
    interativa.

    Atributos:
        name: Nome legível do serviço.
        version: Versão semântica corrente (vem de :data:`app.__version__`).
        docs: Caminho relativo do Swagger UI.

    Example:
        >>> RootResponse(
        ...     name="CloudTask AI SaaS", version="0.1.0", docs="/docs"
        ... ).model_dump()
        {'name': 'CloudTask AI SaaS', 'version': '0.1.0', 'docs': '/docs'}
    """

    name: str = Field(
        ...,
        description="Nome legível do serviço.",
        examples=["CloudTask AI SaaS"],
    )
    version: str = Field(
        ...,
        description="Versão semântica corrente da aplicação.",
        examples=["0.1.0"],
    )
    docs: str = Field(
        ...,
        description="Caminho relativo da interface Swagger UI.",
        examples=["/docs"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "CloudTask AI SaaS",
                    "version": "0.1.0",
                    "docs": "/docs",
                }
            ]
        }
    )


class UploadResponse(BaseModel):
    """Metadados devolvidos depois que um arquivo é armazenado."""

    filename: str = Field(..., description="Nome seguro e único do arquivo armazenado.")
    url: str = Field(..., description="Caminho para baixar o arquivo.")
    size_bytes: int = Field(..., ge=0, description="Tamanho gravado em bytes.")
    storage_mode: Literal["local", "s3"] = Field(
        ..., description="Backend usado para armazenar o arquivo."
    )
