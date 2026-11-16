from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
