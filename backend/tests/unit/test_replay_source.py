from __future__ import annotations

import pytest

from observatorio.producer import replay_source


@pytest.mark.asyncio
async def test_replay_source_queries_historical_months_and_sorts_events(monkeypatch) -> None:
    requested: list[dict] = []

    class FakeResponse:
        def __init__(self, features):
            self.features = features

        def raise_for_status(self):
            return None

        def json(self):
            return {"features": self.features}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params):
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
