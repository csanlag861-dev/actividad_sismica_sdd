from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from observatorio.producer import replay_source


@pytest.mark.asyncio
async def test_replay_source_queries_historical_months_and_sorts_events(monkeypatch) -> None:
    requested: list[dict] = []

    class FakeResponse:
        def __init__(self, features):
            self.status_code = 200
            self.url = "https://example.test/query"
            self.content = json.dumps(
                {"type": "FeatureCollection", "features": features}
            ).encode()

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params, timeout=None):
            requested.append(params)
            if params["starttime"] == "2025-01-01":
                return FakeResponse(
                    [
                        {"id": "later", "properties": {"time": 2_000}},
                        {"id": "earlier", "properties": {"time": 1_000}},
                    ]
                )
            return FakeResponse([])

    monkeypatch.setattr(replay_source.httpx, "AsyncClient", FakeClient)
    events, metadata = await replay_source.fetch_replay_events(
        year=2025,
        min_magnitude=4.0,
        event_type="earthquake",
        url="https://example.test/query",
    )

    assert [event["id"] for event in events] == ["earlier", "later"]
    assert metadata["months_queried"] == 12
    assert metadata["records_received"] == 2
    assert requested[0]["eventtype"] == "earthquake"
    assert requested[0]["minmagnitude"] == "4.0"
    assert requested[0]["orderby"] == "time-asc"


@pytest.mark.asyncio
async def test_saturated_interval_is_subdivided_and_inclusive_overlap_deduplicated(monkeypatch) -> None:
    requested: list[dict] = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    class FakeResponse:
        status_code = 200
        url = "https://example.test/query"

        def __init__(self, features):
            self.content = json.dumps(
                {"type": "FeatureCollection", "features": features}
            ).encode()

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params, timeout=None):
            requested.append(params)
            if len(requested) == 1:
                return FakeResponse(
                    [
                        {"id": f"truncated-{index}", "properties": {"time": index}}
                        for index in range(replay_source.PAGE_SIZE)
                    ]
                )
            return FakeResponse(
                [
                    {"id": "boundary", "properties": {"time": 1, "updated": 1}},
                    {
                        "id": "left" if len(requested) == 2 else "right",
                        "properties": {"time": 2, "updated": len(requested)},
                    },
                ]
            )

    monkeypatch.setattr(replay_source.httpx, "AsyncClient", FakeClient)
    events, metadata = await replay_source.fetch_replay_events(
        year=2025,
        start=start,
        end=end,
        url="https://example.test/query",
    )

    assert replay_source.PAGE_SIZE == 20_000
    assert len(requested) == 3
    assert {event["id"] for event in events} == {"boundary", "left", "right"}
    assert metadata["records_received"] == replay_source.PAGE_SIZE + 4
    assert requested[0]["limit"] == "20000"
    midpoint, right_start = replay_source.split_interval(start, end)
    assert start < midpoint < end
    assert right_start == midpoint
    assert requested[1]["starttime"] == "2025-01-01"
    assert requested[1]["endtime"] == replay_source._format_timestamp(midpoint)
    assert requested[2]["starttime"] == replay_source._format_timestamp(midpoint)
    assert requested[2]["endtime"] == "2025-01-02"


@pytest.mark.asyncio
async def test_saturated_minimum_interval_fails_explicitly(monkeypatch) -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)

    class FakeResponse:
        status_code = 200
        url = "https://example.test/query"
        content = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [{"id": f"event-{i}"} for i in range(replay_source.PAGE_SIZE)],
            }
        ).encode()

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params, timeout=None):
            return FakeResponse()

    monkeypatch.setattr(replay_source.httpx, "AsyncClient", FakeClient)

    with pytest.raises(ValueError, match="cannot be split safely"):
        await replay_source.fetch_replay_events(
            start=start,
            end=start + timedelta(milliseconds=1),
        )
