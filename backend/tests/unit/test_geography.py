from __future__ import annotations

from observatorio.consumer.geography import country_for_coordinates
from observatorio.db.catalog import load_geojson_catalog


def test_natural_earth_catalog_has_unique_country_codes() -> None:
    catalog = load_geojson_catalog()
    codes = [feature["properties"]["ADM0_A3"] for feature in catalog["features"]]
    assert len(codes) >= 170
    assert len(codes) == len(set(codes))


def test_point_in_polygon_assigns_country_and_leaves_ocean_unassigned() -> None:
    assert country_for_coordinates(-3.7, 40.4) == "ESP"
    assert country_for_coordinates(-150.0, 0.0) is None
