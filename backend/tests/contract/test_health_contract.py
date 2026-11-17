from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import OperationalError

from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_health_returns_last_successful_ingestion_and_ignores_its_age(api_context) -> None:
    client, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="old-ingestion",
        event_time=datetime(2020, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2020, 1, 2, tzinfo=timezone.utc),
    )

    response = await client.get("/api/salud")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["last_ingestion"] == 1577923200000


@pytest.mark.asyncio
async def test_health_returns_null_when_no_successful_ingestion_exists(api_context) -> None:
    client, _, _ = api_context

    response = await client.get("/api/salud")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "last_ingestion": None}


@pytest.mark.asyncio
async def test_health_reports_unavailable_bootstrap_without_internal_details(api_context) -> None:
    from observatorio.api import readiness

    client, _, _ = api_context
    readiness.set_ready(False)

    response = await client.get("/api/salud")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "last_ingestion": None}


@pytest.mark.asyncio
async def test_health_database_failure_is_503(api_context) -> None:
    from observatorio.api import readiness
    from observatorio.api.routes import get_db_session

    client, _, app = api_context

    async def broken_session():
        raise OperationalError("SELECT 1", {}, Exception("secret DSN"))
        yield

    app.dependency_overrides[get_db_session] = broken_session
    readiness.set_ready(True)
    response = await client.get("/api/salud")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "last_ingestion": None}
    assert "secret DSN" not in response.text


@pytest.mark.asyncio
async def test_health_reports_missing_required_schema_as_unavailable(api_context) -> None:
    from sqlalchemy import text

    client, factory, _ = api_context
    async with factory() as session:
        await session.execute(text("DROP TABLE alembic_version"))
        await session.commit()

    response = await client.get("/api/salud")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "last_ingestion": None}
