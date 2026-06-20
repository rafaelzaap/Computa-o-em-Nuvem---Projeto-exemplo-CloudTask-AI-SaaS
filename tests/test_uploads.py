from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes_uploads import MAX_UPLOAD_SIZE
from app.core.config import get_settings


def test_upload_local(client: TestClient) -> None:
    response = client.post(
        "/uploads",
        files={"file": ("nuvem.txt", b"ola nuvem", "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["storage_mode"] == "local"
    assert payload["filename"].endswith("-nuvem.txt")
    assert payload["size_bytes"] == 9


def test_upload_local_can_be_downloaded(client: TestClient) -> None:
    uploaded = client.post(
        "/uploads",
        files={"file": ("teste.txt", b"conteudo", "text/plain")},
    ).json()

    response = client.get(uploaded["url"])

    assert response.status_code == 200
    assert response.content == b"conteudo"


def test_upload_sanitizes_filename(client: TestClient) -> None:
    response = client.post(
        "/uploads",
        files={"file": ("../arquivo perigoso.txt", b"seguro", "text/plain")},
    )

    filename = response.json()["filename"]
    assert ".." not in filename
    assert " " not in filename
    assert "/" not in filename


def test_upload_missing_file_returns_422(client: TestClient) -> None:
    response = client.post("/uploads")

    assert response.status_code == 422


def test_upload_too_large_returns_413(client: TestClient) -> None:
    response = client.post(
        "/uploads",
        files={"file": ("grande.bin", b"0" * (MAX_UPLOAD_SIZE + 1))},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == f"File exceeds {MAX_UPLOAD_SIZE} bytes"


def test_upload_unknown_file_returns_404(client: TestClient) -> None:
    response = client.get("/uploads/nao-existe.txt")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_upload_is_written_to_configured_directory(client: TestClient) -> None:
    uploaded = client.post(
        "/uploads",
        files={"file": ("arquivo.txt", b"dados")},
    ).json()
    stored_file = Path(get_settings().local_uploads_dir) / uploaded["filename"]

    assert stored_file.is_file()
    assert stored_file.read_bytes() == b"dados"
