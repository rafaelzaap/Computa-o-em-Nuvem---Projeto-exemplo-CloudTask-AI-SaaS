"""Rotas de upload e download de arquivos."""

from __future__ import annotations

import re
import secrets
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.schemas import UploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def _safe_unique_name(original_name: str | None) -> str:
    """Create a unique filename without trusting a client-provided path."""
    basename = Path(original_name or "upload.bin").name
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", basename).strip("._")
    if not sanitized:
        sanitized = "upload.bin"
    return f"{secrets.token_hex(8)}-{uuid4().hex[:8]}-{sanitized}"


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar arquivo",
)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Store one file locally, rejecting payloads larger than 10 MiB."""
    settings = get_settings()
    if settings.storage_mode != "local":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="S3 storage is not implemented yet",
        )

    upload_dir = Path(settings.local_uploads_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = _safe_unique_name(file.filename)
    destination = upload_dir / stored_name
    size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {MAX_UPLOAD_SIZE} bytes",
                    )
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return UploadResponse(
        filename=stored_name,
        url=f"/uploads/{stored_name}",
        size_bytes=size,
        storage_mode="local",
    )


@router.get(
    "/{filename}",
    response_class=FileResponse,
    summary="Baixar arquivo",
)
def download_file(filename: str) -> FileResponse:
    """Return a locally stored file without allowing path traversal."""
    settings = get_settings()
    if settings.storage_mode != "local":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="S3 storage is not implemented yet",
        )

    if filename != Path(filename).name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    path = Path(settings.local_uploads_dir) / filename
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path=path, filename=filename)
