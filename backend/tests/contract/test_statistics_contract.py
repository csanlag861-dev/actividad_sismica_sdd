from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import OperationalError

from observatorio.models import IngestionInterval

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


async def add_complete_interval(factory, version, start: datetime, end: datetime) -> None:
    async with factory() as session:
        session.add(
            IngestionInterval(
                run_id=version.ingestion_run_id,
                interval_start=start,
                interval_end=end,
                filters={"min_magnitude": None},
                status="complete",
                attempt_count=1,
                records_received=1,
                unique_versions=1,
                published_count=1,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_temporal_comparison_reports_coverage_distributions_and_signed_differences(api_context) -> None:
    from tests.api_support import seed_api_event

    client, factory, _ = api_context
    first_start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    first_end = datetime(2026, 11, 17, 13, tzinfo=timezone.utc)
    second_start = first_end
    second_end = datetime(2026, 11, 17, 14, tzinfo=timezone.utc)
    first = await seed_api_event(
        factory,
        event_id="compare-a",
        event_time=first_start + (first_end - first_start) / 2,
        magnitude=4.0,
        depth_km=10,
    )
    await seed_api_event(
        factory,
        event_id="compare-a-missing",
        event_time=first_start + (first_end - first_start) * 3 / 4,
        magnitude=None,
        depth_km=None,
    )
    second = await seed_api_event(
        factory,
        event_id="compare-b",
        event_time=second_start + (second_end - second_start) / 2,
        magnitude=5.0,
        depth_km=20,
        country_id=None,
    )
    await add_complete_interval(factory, first, first_start, first_end)
    await add_complete_interval(factory, second, second_start, second_end)

    response = await client.post(
        "/api/comparaciones",
        json={
            "mode": "live",
            "filters": {"min_mag": None},
            "groups": [
                {
                    "id": "first",
                    "label": "Primero",
                    "period": {"start": first_start.isoformat(), "end": first_end.isoformat()},
                    "population": {"type": "all"},
                },
                {
                    "id": "second",
                    "label": "Segundo",
                    "period": {"start": second_start.isoformat(), "end": second_end.isoformat()},
                    "population": {"type": "unassigned"},
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "live"
    assert [group["coverage"]["status"] for group in body["groups"]] == ["complete", "complete"]
    assert [group["observed_count"] for group in body["groups"]] == [2, 1]
    assert body["groups"][0]["distributions"]["magnitude"]["missing_count"] == 1
    assert body["groups"][1]["population"]["country_name"] == "Sin país asignado"
    assert body["pairwise_differences"][0]["observed_count_difference"] == -1
    assert body["pairwise_differences"][0]["daily_rate_difference"] < 0
    assert body["pairwise_differences"][0]["distribution_percentage_point_differences"]["magnitude"]


@pytest.mark.asyncio
async def test_temporal_comparison_rejects_malformed_and_invalid_requests(api_context) -> None:
    client, _, _ = api_context
    malformed = await client.post(
        "/api/comparaciones",
        content=b'{"mode":',
        headers={"content-type": "application/json"},
    )
    invalid = await client.post(
        "/api/comparaciones",
        json={
            "mode": "live",
            "groups": [
                {
                    "id": "one",
                    "label": "One",
                    "period": {"start": "2025-01-01T00:00:00", "end": "2025-01-02T00:00:00Z"},
                    "population": {"type": "all"},
                },
                {
                    "id": "two",
                    "label": "Two",
                    "period": {"start": "2025-01-02T00:00:00Z", "end": "2025-01-03T00:00:00Z"},
                    "population": {"type": "all"},
                },
            ],
        },
    )

    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "malformed_request"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["details"][0]["parameter"] == "groups[0].period.start"


@pytest.mark.asyncio
async def test_temporal_comparison_query_failure_identifies_group_without_partial_result(
    api_context,
    monkeypatch,
) -> None:
    from observatorio.api import routes

    client, _, _ = api_context
    calls = 0

    async def fail_second_group(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OperationalError("SELECT", {}, Exception("private database detail"))
        return {"id": "first", "label": "First"}

    monkeypatch.setattr(routes, "build_comparison_group", fail_second_group)
    response = await client.post(
        "/api/comparaciones",
        json={
            "mode": "live",
            "groups": [
                {
                    "id": "first",
                    "label": "First",
                    "period": {"start": "2025-01-01T00:00:00Z", "end": "2025-01-02T00:00:00Z"},
                    "population": {"type": "all"},
                },
                {
                    "id": "second",
                    "label": "Second",
                    "period": {"start": "2025-01-02T00:00:00Z", "end": "2025-01-03T00:00:00Z"},
                    "population": {"type": "all"},
                },
            ],
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["details"] == [
        {"parameter": "groups[1]", "reason": "dependency_unavailable"}
    ]
    assert "private database detail" not in response.text
    assert "pairwise_differences" not in response.json()
