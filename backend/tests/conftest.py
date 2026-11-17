from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def geojson_feature():
    def build_feature(
        event_id: str = "test-event",
        *,
        updated: int = 1_760_000_000_000,
        properties: dict | None = None,
        geometry: dict | None = None,
        **extra: object,
    ) -> dict:
        feature = {
            "type": "Feature",
            "id": event_id,
            "properties": {
                "type": "earthquake",
                "time": updated,
                "updated": updated,
                "mag": 4.1,
                "magType": "ml",
                "place": "test location",
            },
            "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 8.0]},
        }
        feature["properties"].update(properties or {})
        if geometry is not None:
            feature["geometry"] = geometry
        feature.update(extra)
        return feature

    return build_feature


@pytest.fixture
def kafka_envelope(geojson_feature):
    def build_envelope(feature: dict | None = None, **overrides: object) -> dict:
        source_feature = feature or geojson_feature()
        envelope = {
            "id": source_feature.get("id"),
            "mode": "live",
            "source": "usgs-test",
            "ingestion_run_id": "02dfad0c-2c13-431c-95fb-4bdb4d253e23",
            "ingested_at": "2026-11-16T10:00:00+00:00",
            "published_at": "2026-11-16T10:00:01+00:00",
            "payload": source_feature,
        }
        envelope.update(overrides)
        return envelope

    return build_envelope


@pytest_asyncio.fixture
async def api_context(monkeypatch):
    from observatorio.api.app import create_app
    from observatorio.api import readiness
    from observatorio.api.routes import get_db_session
    from observatorio.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('0006_ingestion_intervals')")
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with factory() as session:
            yield session

    app = create_app(allowed_origins=["https://frontend.example"])
    app.dependency_overrides[get_db_session] = override_session
    readiness.set_ready(True)
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client, factory, app
    readiness.set_ready(False)
    await engine.dispose()


@pytest_asyncio.fixture
async def postgres_api_context():
    from observatorio.api.app import create_app
    from observatorio.api import readiness
    from observatorio.api.routes import get_db_session
    from observatorio.config import settings
    from observatorio.models import Base

    database_url = settings.sqlalchemy_database_url
    if not database_url.startswith("postgresql"):
        pytest.skip("PostgreSQL integration requires the Compose database configuration")

    schema = f"api_test_{uuid4().hex}"
    admin_engine = create_async_engine(database_url)
    test_engine = None
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        test_engine = create_async_engine(
            database_url,
            connect_args={"server_settings": {"search_path": schema}},
        )
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(
                text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
            )
            await connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES ('0006_ingestion_intervals')")
            )
        factory = async_sessionmaker(test_engine, expire_on_commit=False)

        async def override_session():
            async with factory() as session:
                yield session

        app = create_app(allowed_origins=["https://frontend.example"])
        app.dependency_overrides[get_db_session] = override_session
        readiness.set_ready(True)
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            yield client, factory, app
    finally:
        readiness.set_ready(False)
        if test_engine is not None:
            await test_engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin_engine.dispose()
