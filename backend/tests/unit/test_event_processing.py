from __future__ import annotations

from observatorio.consumer.processor import process_event


def test_process_event_preserves_coordinates_and_metadata() -> None:
    payload = {
        "id": "evt-001",
        "properties": {"mag": 4.2, "place": "Spain"},
        "geometry": {"coordinates": [-3.0, 40.0, 10.0]},
    }
    out = process_event(payload)
    assert out["event_id"] == "evt-001"
    assert out["latitude"] == 40.0
    assert out["longitude"] == -3.0
    assert out["magnitude"] == 4.2


def test_process_event_rejects_non_mapping() -> None:
    try:
        process_event([1, 2, 3])
    except ValueError:
        return
    raise AssertionError("Expected ValueError for non-dict payload")
