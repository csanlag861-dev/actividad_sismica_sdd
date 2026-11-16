from __future__ import annotations

from observatorio.payloads import payload_fingerprint


def test_payload_fingerprint_is_stable_across_json_key_order(geojson_feature) -> None:
    feature = geojson_feature()
    reordered = {
        "geometry": feature["geometry"],
        "properties": feature["properties"],
        "id": feature["id"],
        "type": feature["type"],
    }

    assert payload_fingerprint(feature) == payload_fingerprint(reordered)


def test_payload_fingerprint_changes_with_source_content(geojson_feature) -> None:
    original = geojson_feature()
    changed = geojson_feature(properties={"mag": 5.2})

    assert payload_fingerprint(original) != payload_fingerprint(changed)


def test_payload_fingerprint_ignores_volatile_envelope_metadata(kafka_envelope) -> None:
    first = kafka_envelope()
    second = kafka_envelope(
        ingested_at="2026-11-16T11:00:00+00:00",
        published_at="2026-11-16T11:00:01+00:00",
    )

    assert payload_fingerprint(first["payload"]) == payload_fingerprint(second["payload"])
