from __future__ import annotations

from types import SimpleNamespace

import pytest

from observatorio import health
from observatorio.api import bootstrap
from observatorio.api.bootstrap import expected_revision


@pytest.mark.asyncio
async def test_producer_and_consumer_readiness_requires_database_and_kafka(monkeypatch) -> None:
    calls: list[str] = []

    async def postgres(name):
        calls.append(f"postgres:{name}")
        return True

    async def kafka():
        calls.append("kafka")
        return True

    monkeypatch.setattr(health, "_check_postgres", postgres)
    monkeypatch.setattr(health, "_check_kafka", kafka)
    assert await health.check_health("productor")
    assert await health.check_health("consumidor")
    assert calls == ["postgres:productor", "kafka", "postgres:consumidor", "kafka"]


def test_expected_alembic_revision_is_current_migration_head() -> None:
    assert expected_revision() == "0002_event_current_version_fk"


@pytest.mark.asyncio
async def test_migration_subprocess_failure_is_not_treated_as_success(monkeypatch) -> None:
    async def failed_to_thread(*args, **kwargs):
        return SimpleNamespace(returncode=1, stderr="migration failed", stdout="")

    monkeypatch.setattr(bootstrap.asyncio, "to_thread", failed_to_thread)
    with pytest.raises(RuntimeError, match="Alembic upgrade failed"):
        await bootstrap._apply_migrations()
