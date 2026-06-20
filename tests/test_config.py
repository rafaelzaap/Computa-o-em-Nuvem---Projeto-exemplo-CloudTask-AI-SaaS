import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.storage_mode == "local"
    assert settings.aws_region == "us-east-1"
    assert settings.s3_presigned_url_expires == 3600


def test_settings_parse_s3_mode() -> None:
    settings = Settings(
        _env_file=None,
        storage_mode="s3",
        s3_bucket_name="example-bucket",
    )

    assert settings.storage_mode == "s3"
    assert settings.s3_bucket_name == "example-bucket"


def test_settings_reject_invalid_storage_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, storage_mode="ftp")
