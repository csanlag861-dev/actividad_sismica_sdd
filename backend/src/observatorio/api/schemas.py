from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: list[dict[str, str]] | None = None


@dataclass(frozen=True)
class QueryFilters:
    start: datetime
    end: datetime
    min_mag: float | None
    country_id: str | None


_ALLOWED_PARAMETERS = {"start", "end", "min_mag", "country_id"}
_MALFORMED_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_COUNTRY_ID = re.compile(r"^[A-Z]{3}$")
_FINITE_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _invalid(parameter: str, reason: str) -> ApiError:
    return ApiError(
        422,
        "invalid_request",
        "Request parameters are invalid",
        [{"parameter": parameter, "reason": reason}],
    )


def parse_query_filters(query_string: bytes, *, now: datetime | None = None) -> QueryFilters:
    if _MALFORMED_PERCENT.search(query_string.decode("latin-1")):
        raise ApiError(400, "malformed_request", "Request syntax is malformed")

    try:
        pairs = parse_qsl(
            query_string.decode("utf-8"),
            keep_blank_values=True,
            strict_parsing=False,
            encoding="utf-8",
            errors="strict",
        )
    except (UnicodeDecodeError, ValueError):
        raise ApiError(400, "malformed_request", "Request syntax is malformed") from None

    values: dict[str, str] = {}
    for key, value in pairs:
        if key not in _ALLOWED_PARAMETERS:
            raise _invalid("query", "contains an unknown query parameter")
        if key in values:
            raise _invalid(key, "must be specified at most once")
        values[key] = value

    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    instant = instant.astimezone(timezone.utc)

    def parse_datetime(parameter: str, raw: str | None, default: datetime) -> datetime:
        if raw is None:
            return default
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            raise _invalid(parameter, "must be a valid ISO 8601 timestamp") from None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise _invalid(parameter, "must include a timezone offset")
        return parsed.astimezone(timezone.utc)

    start = parse_datetime("start", values.get("start"), instant - timedelta(hours=24))
    end = parse_datetime("end", values.get("end"), instant)
    if start >= end:
        raise _invalid("start", "must be earlier than end")

    min_mag = None
    if "min_mag" in values:
        if not _FINITE_NUMBER.fullmatch(values["min_mag"]):
            raise _invalid("min_mag", "must be a finite number")
        try:
            min_mag = float(values["min_mag"])
        except ValueError:
            raise _invalid("min_mag", "must be a finite number") from None
        if not math.isfinite(min_mag):
            raise _invalid("min_mag", "must be a finite number")

    country_id = values.get("country_id")
    if country_id is not None and not _COUNTRY_ID.fullmatch(country_id):
        raise _invalid("country_id", "must be a three-letter uppercase country identifier")

    return QueryFilters(start, end, min_mag, country_id)


def iso_utc(value: datetime) -> str:
    normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z")


def epoch_milliseconds(value: datetime | None) -> int | None:
    if value is None:
        return None
    normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return int(normalized.timestamp() * 1000)
