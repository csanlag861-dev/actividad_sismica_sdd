from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from observatorio.api import readiness
from observatorio.api.app import create_app
from observatorio.api.routes import get_db_session


@pytest.mark.asyncio
async def test_api_serves_health_while_bootstrap_is_unavailable(api_context, monkeypatch) -> None:
    from observatorio.api import app as app_module

    _, factory, _ = api_context
    bootstrap_started = asyncio.Event()
    keep_running = asyncio.Event()

    async def unavailable_bootstrap():
        readiness.set_ready(False)
        bootstrap_started.set()
        await keep_running.wait()

    monkeypatch.setattr(app_module, "bootstrap_backend", unavailable_bootstrap)
    application = create_app(allowed_origins=[])

    async def override_session():
        async with factory() as session:
            yield session

    application.dependency_overrides[get_db_session] = override_session
    async with application.router.lifespan_context(application):
        await bootstrap_started.wait()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/salud")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "last_ingestion": None}
