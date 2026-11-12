from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from observatorio.models.reference import Country


def geojson_catalog_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "ne_110m_admin_0_countries.geojson"


def load_geojson_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or geojson_catalog_path()
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Natural Earth GeoJSON catalog not found: {catalog_path}")

    raw_data = catalog_path.read_bytes()
    if catalog_path.resolve() == geojson_catalog_path().resolve():
        manifest_path = catalog_path.parent / "geodata_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual_hash = hashlib.sha256(raw_data).hexdigest()
        if actual_hash != manifest.get("sha256"):
            raise ValueError(f"Natural Earth GeoJSON checksum does not match {manifest_path}")
    payload = json.loads(raw_data)
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError(f"Invalid GeoJSON FeatureCollection in {catalog_path}")

    seen: set[str] = set()
    for feature in payload["features"]:
        properties = feature.get("properties") or {}
        country_id = properties.get("ADM0_A3")
        if not isinstance(country_id, str) or len(country_id) != 3:
            raise ValueError(f"Natural Earth feature has invalid ADM0_A3 code: {country_id!r}")
        if country_id in seen:
            raise ValueError(f"Natural Earth ADM0_A3 code is not unique: {country_id}")
        seen.add(country_id)
        if not isinstance(feature.get("geometry"), dict):
            raise ValueError(f"Natural Earth feature {country_id} has no geometry")
    return payload


async def ensure_country_catalog(session: AsyncSession) -> list[Country]:
    payload = load_geojson_catalog()
    inserted_or_updated: list[Country] = []
    for feature in payload["features"]:
        properties = feature["properties"]
        country_id = properties["ADM0_A3"]
        country_name = str(properties.get("NAME_ES") or properties.get("ADMIN") or country_id).strip()
        country = await session.get(Country, country_id)
        if country is None:
            country = Country(country_id=country_id, country_name=country_name)
            session.add(country)
        else:
            country.country_name = country_name
        inserted_or_updated.append(country)
    await session.commit()
    return inserted_or_updated
