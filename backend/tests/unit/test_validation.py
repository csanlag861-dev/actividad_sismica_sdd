from __future__ import annotations

import pytest

from observatorio.consumer.validation import normalize_event


def test_valid_feature_preserves_optional_nulls(geojson_feature, kafka_envelope) -> None:
    feature = geojson_feature(
        properties={"mag": None, "magType": None, "place": None},
        geometry={"type": "Point", "coordinates": [10.0, 20.0, None]},
    )

    valid, reason, event = normalize_event(kafka_envelope(feature))

    assert valid is True
    assert reason is None
    assert event["magnitude"] is None
    assert event["mag_type"] is None
    assert event["place"] is None
    assert event["depth_km"] is None
    assert event["original_payload"] == feature


def test_non_earthquake_is_classified_as_an_exclusion(geojson_feature, kafka_envelope) -> None:
    feature = geojson_feature(properties={"type": "quarry blast"})

    valid, reason, _ = normalize_event(kafka_envelope(feature))

    assert valid is False
    assert reason == "event_type_excluded"


def test_non_feature_geometry_and_invalid_coordinates_are_rejected(geojson_feature, kafka_envelope) -> None:
    wrong_type = geojson_feature(type="NotAFeature")
    wrong_geometry = geojson_feature(geometry={"type": "Polygon", "coordinates": []})
    bad_coordinates = geojson_feature(geometry={"type": "Point", "coordinates": [181, 0]})

    assert normalize_event(kafka_envelope(wrong_type))[1] == "invalid_feature_type"
    assert normalize_event(kafka_envelope(wrong_geometry))[1] == "invalid_geometry_type"
    assert normalize_event(kafka_envelope(bad_coordinates))[1] == "coordinates_out_of_range"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("magType", {"unexpected": "object"}, "invalid_mag_type"),
        ("magType", ["unexpected", "list"], "invalid_mag_type"),
        ("place", {"unexpected": "object"}, "invalid_place"),
        ("place", ["unexpected", "list"], "invalid_place"),
    ],
)
def test_optional_text_fields_reject_non_string_values(
    geojson_feature,
    kafka_envelope,
    field: str,
    value: object,
    reason: str,
) -> None:
    feature = geojson_feature(properties={field: value})

    valid, actual_reason, _ = normalize_event(kafka_envelope(feature))

    assert valid is False
    assert actual_reason == reason
