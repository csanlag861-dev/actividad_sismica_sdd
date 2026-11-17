from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from observatorio import healthcheck


@pytest.mark.asyncio
async def test_api_healthcheck_requires_http_api_and_ready_response(monkeypatch) -> None:
    class HealthyClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, _path):
            return SimpleNamespace(status_code=200)

    monkeypatch.setattr(healthcheck.httpx, "AsyncClient", HealthyClient)

    assert await healthcheck.check_service("api")


@pytest.mark.asyncio
async def test_api_healthcheck_is_unhealthy_during_bootstrap_or_connection_failure(monkeypatch) -> None:
    class UnavailableClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, _path):
            return SimpleNamespace(status_code=503)

    monkeypatch.setattr(healthcheck.httpx, "AsyncClient", UnavailableClient)
    assert not await healthcheck.check_service("api")

    class DisconnectedClient(UnavailableClient):
        async def get(self, _path):
            raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(healthcheck.httpx, "AsyncClient", DisconnectedClient)
    assert not await healthcheck.check_service("api")
