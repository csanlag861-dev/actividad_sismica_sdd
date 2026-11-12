from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape

from observatorio.db.catalog import geojson_catalog_path, load_geojson_catalog


@lru_cache(maxsize=2)
def _country_shapes(path: str) -> tuple[tuple[str, object], ...]:
    catalog = load_geojson_catalog(Path(path))
    return tuple(
        (feature["properties"]["ADM0_A3"], shape(feature["geometry"]))
        for feature in catalog["features"]
    )


def country_for_coordinates(longitude: float, latitude: float, catalog_path: Path | None = None) -> str | None:
    path = str(catalog_path or geojson_catalog_path())
    point = Point(longitude, latitude)
    matches = [
        country_id
        for country_id, polygon in _country_shapes(path)
        if polygon.covers(point)
    ]
    return matches[0] if len(matches) == 1 else None


def resolve_country_id(event: dict, country_catalog: dict[str, str] | None = None) -> str | None:
    longitude = event.get("longitude")
    latitude = event.get("latitude")
    if longitude is None or latitude is None:
        return None
    return country_for_coordinates(float(longitude), float(latitude))


def country_matches_place(place_name: str, country_catalog: dict[str, str] | None = None) -> str | None:
    if not place_name or not country_catalog:
        return None
    normalized = place_name.strip().casefold()
    matches = [
        code
        for code, country_name in country_catalog.items()
        if country_name and country_name.strip().casefold() == normalized
    ]
    return matches[0] if len(matches) == 1 else None
