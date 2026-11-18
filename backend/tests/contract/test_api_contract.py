from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from sqlalchemy.exc import OperationalError

from observatorio.api.routes import get_db_session
from observatorio.models import EventVersion
from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_events_contract_filters_and_serializes_unknown_depth(api_context) -> None:
    client, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="boundary",
        event_time=datetime(2026, 11, 17, 12, tzinfo=timezone.utc),
        magnitude=4.0,
        depth_km=None,
    )

    response = await client.get(
        "/api/eventos",
        params={
            "start": "2026-11-17T12:00:00Z",
            "end": "2026-11-17T13:00:00Z",
            "min_mag": "4",
            "country_id": "ESP",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["mode"] == "live"
    assert body["metadata"]["count"] == 1
    assert body["metadata"]["truncated"] is False
    assert body["features"][0]["geometry"]["coordinates"] == [-3.7, 40.4]
    assert body["features"][0]["properties"]["depth_km"] is None


@pytest.mark.asyncio
async def test_events_contract_selects_replay_without_mixing_live(api_context) -> None:
    client, factory, _ = api_context
    replay_time = datetime(2025, 6, 1, 12, tzinfo=timezone.utc)
    await seed_api_event(
        factory,
        event_id="live-only",
        event_time=replay_time,
        mode="live",
    )
    await seed_api_event(
        factory,
        event_id="replay-only",
        event_time=replay_time,
        mode="replay",
    )

    response = await client.get(
        "/api/eventos",
        params={
            "mode": "replay",
            "start": "2025-06-01T00:00:00Z",
            "end": "2025-06-02T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["mode"] == "replay"
    assert [feature["id"] for feature in body["features"]] == ["replay-only"]
    assert body["features"][0]["properties"]["traceability"]["mode"] == "replay"


@pytest.mark.asyncio
async def test_events_contract_exposes_safe_version_traceability(api_context) -> None:
    client, factory, _ = api_context
    version_time = datetime(2026, 11, 17, 12, 30, tzinfo=timezone.utc)
    version = await seed_api_event(
        factory,
        event_id="traceable",
        event_time=version_time,
        updated_at=version_time,
    )

    response = await client.get(
        "/api/eventos",
        params={
            "start": "2026-11-17T12:00:00Z",
            "end": "2026-11-17T13:00:00Z",
        },
    )

    assert response.status_code == 200
    feature = response.json()["features"][0]
    assert feature["id"] == "traceable"
    assert feature["properties"]["updated"] == int(version_time.timestamp() * 1000)
    assert feature["properties"]["traceability"] == {
        "mode": "live",
        "source": "usgs-live",
        "ingested_at": int(version.ingested_at.timestamp() * 1000),
        "ingestion_run_id": str(version.ingestion_run_id),
    }
    assert "original_payload" not in feature
    assert "original_payload" not in feature["properties"]
    assert "payload_sha256" not in feature["properties"]
    assert "payload_sha256" not in feature["properties"]["traceability"]


@pytest.mark.asyncio
async def test_events_contract_hides_unrecognized_traceability_source(api_context) -> None:
    client, factory, _ = api_context
    await seed_api_event(factory, event_id="unknown-source")
    async with factory() as session:
        await session.execute(
            update(EventVersion)
            .where(EventVersion.event_id == "unknown-source")
            .values(source="unrecognized-source")
        )
        await session.commit()

    response = await client.get(
        "/api/eventos",
        params={
            "start": "2026-11-17T00:00:00Z",
            "end": "2026-11-18T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["features"][0]["properties"]["traceability"]["source"] is None


@pytest.mark.asyncio
async def test_empty_collection_and_invalid_query_errors_are_distinct(api_context) -> None:
    client, _, _ = api_context

    empty = await client.get(
        "/api/eventos",
        params={"start": "2026-11-16T00:00:00Z", "end": "2026-11-17T00:00:00Z"},
    )
    invalid = await client.get("/api/eventos?unexpected=value")
    malformed = await client.get("/api/eventos?start=%ZZ")

    assert empty.status_code == 200
    assert empty.json()["features"] == []
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_request"
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "malformed_request"


@pytest.mark.asyncio
async def test_filters_combine_with_and_and_country_match_is_exact(api_context) -> None:
    from tests.api_support import seed_api_event

    client, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="spain",
        event_time=datetime(2026, 11, 17, 12, 15, tzinfo=timezone.utc),
        magnitude=4.0,
        country_id="ESP",
    )
    await seed_api_event(
        factory,
        event_id="france",
        event_time=datetime(2026, 11, 17, 12, 15, tzinfo=timezone.utc),
        magnitude=4.0,
        country_id="FRA",
    )

    response = await client.get(
        "/api/eventos",
        params={
            "start": "2026-11-17T12:00:00Z",
            "end": "2026-11-17T13:00:00Z",
            "min_mag": "4",
            "country_id": "ESP",
        },
    )

    assert response.status_code == 200
    assert [feature["id"] for feature in response.json()["features"]] == ["spain"]


@pytest.mark.asyncio
async def test_unknown_country_code_uses_common_invalid_request_envelope(api_context) -> None:
    client, _, _ = api_context

    response = await client.get("/api/eventos", params={"country_id": "ZZZ"})

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_request",
        "message": "Request parameters are invalid",
        "details": [
            {"parameter": "country_id", "reason": "is not present in the country catalog"}
        ],
    }


@pytest.mark.asyncio
async def test_default_window_covers_the_last_24_hours(api_context) -> None:
    client, factory, _ = api_context
    now = datetime.now(timezone.utc)
    await seed_api_event(
        factory,
        event_id="inside-default-window",
        event_time=now - timedelta(hours=1),
    )
    await seed_api_event(
        factory,
        event_id="outside-default-window",
        event_time=now - timedelta(hours=25),
    )

    response = await client.get("/api/eventos")

    assert response.status_code == 200
    assert [feature["id"] for feature in response.json()["features"]] == [
        "inside-default-window"
    ]


@pytest.mark.asyncio
async def test_start_is_inclusive_end_exclusive_and_minimum_magnitude_is_inclusive(api_context) -> None:
    client, factory, _ = api_context
    start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    end = datetime(2026, 11, 17, 13, tzinfo=timezone.utc)
    for event_id, event_time, magnitude in (
        ("at-start", start, 4.0),
        ("below-minimum", start + timedelta(minutes=10), 3.9),
        ("missing-magnitude", start + timedelta(minutes=20), None),
        ("at-end", end, 5.0),
    ):
        await seed_api_event(
            factory,
            event_id=event_id,
            event_time=event_time,
            magnitude=magnitude,
        )

    response = await client.get(
        "/api/eventos",
        params={
            "start": start.isoformat(),
            "end": end.isoformat(),
            "min_mag": "4",
        },
    )

    assert response.status_code == 200
    assert [feature["id"] for feature in response.json()["features"]] == ["at-start"]


@pytest.mark.asyncio
async def test_events_pagination_has_total_stable_order_and_true_truncation(api_context) -> None:
    client, factory, _ = api_context
    start = datetime(2026, 11, 17, tzinfo=timezone.utc)
    for index in range(30):
        await seed_api_event(
            factory,
            event_id=f"event-{index:02}",
            event_time=start + timedelta(minutes=index // 2),
        )

    params = {"start": start.isoformat(), "end": (start + timedelta(days=1)).isoformat()}
    first = await client.get("/api/eventos", params={**params, "limit": 25})
    second = await client.get("/api/eventos", params={**params, "limit": 25, "offset": 25})
    out_of_range = await client.get("/api/eventos", params={**params, "limit": 25, "offset": 30})

    assert first.status_code == second.status_code == out_of_range.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["metadata"]["total_count"] == 30
    assert first_body["metadata"]["offset"] == 0
    assert first_body["metadata"]["limit"] == 25
    assert first_body["metadata"]["count"] == 25
    assert first_body["metadata"]["truncated"] is True
    assert second_body["metadata"]["count"] == 5
    assert second_body["metadata"]["total_count"] == 30
    assert second_body["metadata"]["truncated"] is True
    assert [feature["id"] for feature in first_body["features"][:2]] == ["event-28", "event-29"]
    assert [feature["id"] for feature in first_body["features"] + second_body["features"]] == [
        f"event-{index:02}"
        for pair in reversed(range(15))
        for index in (pair * 2, pair * 2 + 1)
    ]
    assert out_of_range.json()["metadata"]["total_count"] == 30
    assert out_of_range.json()["features"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["limit=24", "limit=25.0", "offset=-1", "offset=1.5"])
async def test_events_reject_invalid_pagination_parameters(api_context, query: str) -> None:
    client, _, _ = api_context

    response = await client.get(f"/api/eventos?{query}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.asyncio
async def test_storage_failure_is_not_an_empty_success(api_context) -> None:
    client, _, app = api_context

    async def broken_session():
        raise OperationalError("SELECT 1", {}, Exception("private database detail"))
        yield

    app.dependency_overrides[get_db_session] = broken_session
    response = await client.get("/api/eventos")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "dependency_unavailable"
    assert "private database detail" not in response.text


@pytest.mark.asyncio
async def test_unexpected_api_failure_uses_safe_internal_error_envelope(api_context) -> None:
    client, _, app = api_context

    async def broken_session():
        raise ValueError("private internal detail")
        yield

    app.dependency_overrides[get_db_session] = broken_session
    response = await client.get("/api/eventos")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["message"] == "The request could not be completed"
    assert "private internal detail" not in response.text
