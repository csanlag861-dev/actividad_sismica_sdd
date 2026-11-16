from __future__ import annotations

import pytest

from observatorio.config import Settings, get_settings


def test_postgres_requires_a_runtime_password() -> None:
    settings = Settings(postgres_host="postgres", postgres_password="")

    with pytest.raises(ValueError, match="POSTGRES_PASSWORD is required"):
        settings.validate()


def test_local_configuration_uses_sqlite_without_postgres_credentials(monkeypatch) -> None:
    for name in ("POSTGRES_HOST", "POSTGRES_PASSWORD", "DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.postgres_host == ""
    assert settings.postgres_password == ""
    assert settings.postgres_dsn == "sqlite+aiosqlite:///./observatorio.db"


def test_postgres_dsn_uses_supplied_password() -> None:
    settings = Settings(postgres_host="postgres", postgres_password="runtime-value")

    assert settings.postgres_dsn == (
        "postgresql+asyncpg://observatorio:runtime-value@postgres:5432/observatorio"
    )
