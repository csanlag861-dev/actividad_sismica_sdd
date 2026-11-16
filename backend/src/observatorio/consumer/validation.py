from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        try:
            parsed = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def normalize_event(message: Any) -> tuple[bool, str | None, dict[str, Any]]:
    if not isinstance(message, Mapping):
        return False, "invalid_mapping", {}

    envelope = message
    raw_event = message.get("payload", message)
    if not isinstance(raw_event, Mapping):
        return False, "invalid_payload", {}
    if raw_event.get("type") != "Feature":
        return False, "invalid_feature_type", {}
    properties = raw_event.get("properties")
    geometry = raw_event.get("geometry")
    if not isinstance(properties, Mapping):
        return False, "invalid_properties", {}
    if not isinstance(geometry, Mapping):
        return False, "invalid_geometry", {}
    if geometry.get("type") != "Point":
        return False, "invalid_geometry_type", {}

    event_id = raw_event.get("id")
    if not isinstance(event_id, str) or not event_id.strip():
        return False, "missing_event_id", {}
    envelope_id = envelope.get("id")
    if not isinstance(envelope_id, str) or not envelope_id.strip():
        return False, "missing_envelope_id", {}
    if envelope_id != event_id:
        return False, "event_id_mismatch", {}

    event_type = properties.get("type")
    if not isinstance(event_type, str) or not event_type.strip():
        return False, "missing_event_type", {}
    if event_type != "earthquake":
        return False, "event_type_excluded", {}

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, (list, tuple)) or len(coordinates) < 2:
        return False, "missing_coordinates", {}
    longitude = _finite_float(coordinates[0])
    latitude = _finite_float(coordinates[1])
    if longitude is None or latitude is None:
        return False, "invalid_coordinates", {}
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        return False, "coordinates_out_of_range", {}
    raw_depth = coordinates[2] if len(coordinates) > 2 else None
    depth = _finite_float(raw_depth)
    if raw_depth is not None and depth is None:
        return False, "invalid_depth", {}

    raw_magnitude = properties.get("mag")
    magnitude = _finite_float(raw_magnitude)
    if raw_magnitude is not None and magnitude is None:
        return False, "invalid_magnitude", {}
    mag_type = properties.get("magType")
    if mag_type is not None and not isinstance(mag_type, str):
        return False, "invalid_mag_type", {}
    place = properties.get("place")
    if place is not None and not isinstance(place, str):
        return False, "invalid_place", {}

    event_time = _parse_datetime(properties.get("time"))
    updated_at = _parse_datetime(properties.get("updated"))
    if event_time is None or updated_at is None:
        return False, "invalid_event_timestamps", {}

    mode = envelope.get("mode")
    if not isinstance(mode, str) or mode not in {"live", "replay"}:
        return False, "invalid_mode", {}
    source = envelope.get("source")
    if not isinstance(source, str) or not source.strip():
        return False, "missing_source", {}

    run_id = envelope.get("ingestion_run_id")
    try:
        run_uuid = UUID(str(run_id)) if run_id is not None else None
    except (ValueError, TypeError, AttributeError):
        return False, "invalid_ingestion_run_id", {}
    if run_uuid is None:
        return False, "invalid_ingestion_run_id", {}

    ingested_at = _parse_datetime(envelope.get("ingested_at"))
    if ingested_at is None:
        return False, "invalid_ingested_at", {}
    return True, None, {
        "mode": mode,
        "event_id": event_id.strip(),
        "updated_at": updated_at,
        "event_time": event_time,
        "magnitude": magnitude,
        "mag_type": mag_type,
        "place": place,
        "longitude": longitude,
        "latitude": latitude,
        "depth_km": depth,
        "source": source,
        "ingested_at": ingested_at,
        "ingestion_run_id": run_uuid,
        "original_payload": dict(raw_event),
    }


def validate_event(raw_event: Any) -> tuple[bool, str | None, dict[str, Any]]:
    return normalize_event(raw_event)
