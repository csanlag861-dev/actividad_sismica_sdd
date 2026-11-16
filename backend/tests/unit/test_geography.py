from __future__ import annotations

import json

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


def test_boundary_or_multiple_polygon_matches_remain_unassigned(tmp_path) -> None:
    square = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    catalog_path = tmp_path / "overlap.geojson"
    catalog_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "ADM0_A3": code,
                            "NAME_ES": code,
                            "ADMIN": code,
                            "CONTINENT": "Test",
                            "SUBREGION": "Test",
                        },
                        "geometry": square,
                    }
                    for code in ("AAA", "BBB")
                ],
            }
        ),
        encoding="utf-8",
    )

    assert country_for_coordinates(0.5, 0.5, catalog_path) is None
    assert country_for_coordinates(0.0, 0.5, catalog_path) is None
