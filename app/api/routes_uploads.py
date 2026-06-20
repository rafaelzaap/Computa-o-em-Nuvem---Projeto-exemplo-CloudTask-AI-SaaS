"""Rotas de upload e download de arquivos."""

from __future__ import annotations

import re
import secrets
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse

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


def _s3_client(region: str):
    """Build an S3 client using the standard AWS credential chain."""
    return boto3.client("s3", region_name=region)


def _require_bucket(bucket_name: str) -> str:
    """Fail with a clear message when S3 mode lacks a bucket."""
    if not bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3_BUCKET_NAME is not configured",
        )
    return bucket_name


async def _read_limited(file: UploadFile) -> bytes:
    """Read at most 10 MiB and always close the temporary upload."""
    content = bytearray()
    try:
        while chunk := await file.read(CHUNK_SIZE):
            content.extend(chunk)
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {MAX_UPLOAD_SIZE} bytes",
                )
    finally:
        await file.close()
    return bytes(content)


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar arquivo",
)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Store one file locally or in S3, enforcing the same size limit."""
    settings = get_settings()
    stored_name = _safe_unique_name(file.filename)
    content_type = file.content_type or "application/octet-stream"
    content = await _read_limited(file)

    if settings.storage_mode == "local":
        upload_dir = Path(settings.local_uploads_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        (upload_dir / stored_name).write_bytes(content)
        url = f"/uploads/{stored_name}"
    else:
        bucket = _require_bucket(settings.s3_bucket_name)
        client = _s3_client(settings.aws_region)
        try:
            client.put_object(
                Bucket=bucket,
                Key=stored_name,
                Body=content,
                ContentType=content_type,
            )
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": stored_name},
                ExpiresIn=settings.s3_presigned_url_expires,
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not store file in S3",
            ) from exc

    return UploadResponse(
        filename=stored_name,
        url=url,
        size_bytes=len(content),
        storage_mode=settings.storage_mode,
    )


@router.get(
    "/{filename}",
    response_model=None,
    summary="Baixar arquivo",
)
def download_file(filename: str) -> FileResponse | RedirectResponse:
    """Return a local file or redirect the client to a presigned S3 URL."""
    settings = get_settings()
    if filename != Path(filename).name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if settings.storage_mode == "local":
        path = Path(settings.local_uploads_dir) / filename
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return FileResponse(path=path, filename=filename)

    bucket = _require_bucket(settings.s3_bucket_name)
    client = _s3_client(settings.aws_region)
    try:
        client.head_object(Bucket=bucket, Key=filename)
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": filename},
            ExpiresIn=settings.s3_presigned_url_expires,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not access file in S3",
        ) from exc
    except BotoCoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not access file in S3",
        ) from exc

    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
