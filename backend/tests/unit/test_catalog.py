from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.db.catalog import ensure_country_catalog, load_geojson_catalog
from observatorio.models import Base, Country


def test_catalog_exposes_all_required_unmodified_attributes() -> None:
    catalog = load_geojson_catalog()
    spain = next(
        feature
        for feature in catalog["features"]
        if feature["properties"]["ADM0_A3"] == "ESP"
    )
    properties = spain["properties"]

    assert properties["NAME_ES"]
    assert properties["ADMIN"]
    assert properties["CONTINENT"]
    assert properties["SUBREGION"]


@pytest.mark.asyncio
async def test_catalog_loader_persists_verified_attributes() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        await ensure_country_catalog(session)
        spain = await session.get(Country, "ESP")

    assert spain is not None
    assert spain.country_name
    assert spain.name_es
    assert spain.admin
    assert spain.continent
    assert spain.subregion
    await engine.dispose()
