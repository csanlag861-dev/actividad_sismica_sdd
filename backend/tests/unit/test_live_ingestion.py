from __future__ import annotations

import asyncio

import httpx
import pytest

from observatorio.producer import live, source


@pytest.mark.asyncio
async def test_live_request_retries_rate_limits_and_validates_geojson(monkeypatch) -> None:
    responses = [429, 503, 200]
    requested_timeouts: list[float] = []
    delays: list[float] = []

    class FakeResponse:
        def __init__(self, status_code: int):
            self.response = httpx.Response(
                status_code,
                request=httpx.Request("GET", "https://example.test/feed"),
                content=b'{"type":"FeatureCollection","features":[]}',
            )
            self.status_code = self.response.status_code
            self.content = self.response.content
            self.url = self.response.url

        def raise_for_status(self):
            self.response.raise_for_status()

        def json(self):
            return {"type": "FeatureCollection", "features": []}

    class FakeClient:
        def __init__(self, *, timeout):
            requested_timeouts.append(timeout)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            return FakeResponse(responses.pop(0))

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(source.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(source.asyncio, "sleep", fake_sleep)

    result = await source.fetch_recent_response("https://example.test/feed")

    assert result.status_code == 200
    assert result.attempts == 3
    assert requested_timeouts == [8.0]
    assert delays == [1.0, 2.0]


@pytest.mark.asyncio
async def test_live_request_does_not_retry_other_4xx(monkeypatch) -> None:
    requests = 0
    response = httpx.Response(
        400,
        request=httpx.Request("GET", "https://example.test/feed"),
    )

    class FakeClient:
        def __init__(self, *, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            nonlocal requests
            requests += 1
            return response

    monkeypatch.setattr(source.httpx, "AsyncClient", FakeClient)

    with pytest.raises(httpx.HTTPStatusError):
        await source.fetch_recent_response("https://example.test/feed")
    assert requests == 1


@pytest.mark.asyncio
async def test_live_request_retries_unparseable_json(monkeypatch) -> None:
    contents = [
        b"not-json",
        b'{"type":"FeatureCollection","features":[]}',
    ]
    delays: list[float] = []

    class FakeResponse:
        status_code = 200
        url = httpx.URL("https://example.test/feed")

        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            return FakeResponse(contents.pop(0))

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(source.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(source.asyncio, "sleep", fake_sleep)

    result = await source.fetch_recent_response("https://example.test/feed")
    assert result.attempts == 2
    assert delays == [1.0]


@pytest.mark.asyncio
async def test_live_loop_uses_monotonic_deadlines_without_catch_up_bursts(monkeypatch) -> None:
    clock = 0.0
    tick_starts: list[float] = []
    sleeps: list[float] = []

    async def tick() -> list[dict]:
        nonlocal clock
        tick_starts.append(clock)
        if len(tick_starts) == 1:
            clock += 130.0
        elif len(tick_starts) == 2:
            raise asyncio.CancelledError
        return []

    async def fake_sleep(delay: float) -> None:
        nonlocal clock
        sleeps.append(delay)
        clock += delay

    with pytest.raises(asyncio.CancelledError):
        await live.run_loop(tick=tick, sleep=fake_sleep, monotonic=lambda: clock)

    assert tick_starts == [0.0, 180.0]
    assert sleeps == [50.0]
