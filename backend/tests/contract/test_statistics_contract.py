from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import OperationalError

from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_statistics_contract_reports_valid_percentages_and_missing_values(api_context) -> None:
    client, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="valid",
        event_time=datetime(2026, 11, 17, 12, 15, tzinfo=timezone.utc),
        magnitude=4.0,
        depth_km=10.0,
    )
    await seed_api_event(
        factory,
        event_id="missing",
        event_time=datetime(2026, 11, 17, 12, 30, tzinfo=timezone.utc),
        magnitude=None,
        depth_km=None,
        country_id=None,
    )

    response = await client.get(
        "/api/estadisticas",
        params={"start": "2026-11-17T12:00:00Z", "end": "2026-11-17T13:00:00Z"},
    )

    assert response.status_code == 200
    body = response.json()
    magnitude = body["distributions"]["magnitude"]
    assert magnitude["valid_count"] == 1
    assert magnitude["missing_count"] == 1
    assert sum(bucket["count"] for bucket in magnitude["buckets"]) == 1
    assert sum(bucket["percentage"] for bucket in magnitude["buckets"]) == 100
    assert body["country_counts"]["missing_count"] == 1


@pytest.mark.asyncio
async def test_statistics_zero_valid_values_use_null_percentages(api_context) -> None:
    client, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="only-missing",
        event_time=datetime(2026, 11, 17, 12, 15, tzinfo=timezone.utc),
        magnitude=None,
    )

    response = await client.get(
        "/api/estadisticas",
        params={"start": "2026-11-17T12:00:00Z", "end": "2026-11-17T13:00:00Z"},
    )
    magnitude = response.json()["distributions"]["magnitude"]

    assert response.status_code == 200
    assert magnitude["valid_count"] == 0
    assert magnitude["buckets"] == []


@pytest.mark.asyncio
async def test_statistics_storage_error_uses_common_envelope(api_context) -> None:
    from observatorio.api.routes import get_db_session

    client, _, app = api_context

    async def broken_session():
        raise OperationalError("SELECT 1", {}, Exception("internal detail"))
        yield

    app.dependency_overrides[get_db_session] = broken_session
    response = await client.get("/api/estadisticas")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "dependency_unavailable"
    assert "internal detail" not in response.text
