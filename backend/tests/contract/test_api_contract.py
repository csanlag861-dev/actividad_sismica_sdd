from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import OperationalError

from observatorio.api.routes import get_db_session
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
