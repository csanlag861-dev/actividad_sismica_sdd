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


@dataclass(frozen=True)
class EventPageRequest:
    filters: QueryFilters
    limit: int
    offset: int


@dataclass(frozen=True)
class ComparisonPopulation:
    type: str
    country_id: str | None


@dataclass(frozen=True)
class ComparisonGroup:
    group_id: str
    label: str
    start: datetime
    end: datetime
    population: ComparisonPopulation


@dataclass(frozen=True)
class ComparisonRequest:
    mode: str
    min_mag: float | None
    groups: tuple[ComparisonGroup, ...]


_FILTER_PARAMETERS = {"start", "end", "min_mag", "country_id"}
_EVENT_PARAMETERS = _FILTER_PARAMETERS | {"limit", "offset"}
_MALFORMED_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_COUNTRY_ID = re.compile(r"^[A-Z]{3}$")
_FINITE_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_NON_NEGATIVE_INTEGER = re.compile(r"^\d+$")


def _invalid(parameter: str, reason: str) -> ApiError:
    return ApiError(
        422,
        "invalid_request",
        "Request parameters are invalid",
        [{"parameter": parameter, "reason": reason}],
    )


def _query_values(query_string: bytes, allowed_parameters: set[str]) -> dict[str, str]:
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
        if key not in allowed_parameters:
            raise _invalid("query", "contains an unknown query parameter")
        if key in values:
            raise _invalid(key, "must be specified at most once")
        values[key] = value

    return values


def _parse_filters(
    values: dict[str, str],
    *,
    now: datetime | None = None,
) -> QueryFilters:
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


def parse_query_filters(query_string: bytes, *, now: datetime | None = None) -> QueryFilters:
    return _parse_filters(_query_values(query_string, _FILTER_PARAMETERS), now=now)


def parse_event_page_request(
    query_string: bytes,
    *,
    now: datetime | None = None,
) -> EventPageRequest:
    values = _query_values(query_string, _EVENT_PARAMETERS)
    filters = _parse_filters(
        {key: value for key, value in values.items() if key in _FILTER_PARAMETERS},
        now=now,
    )

    raw_limit = values.get("limit", "25")
    if not _NON_NEGATIVE_INTEGER.fullmatch(raw_limit):
        raise _invalid("limit", "must be one of 25, 50, or 100")
    limit = int(raw_limit)
    if limit not in {25, 50, 100}:
        raise _invalid("limit", "must be one of 25, 50, or 100")

    raw_offset = values.get("offset", "0")
    if not _NON_NEGATIVE_INTEGER.fullmatch(raw_offset):
        raise _invalid("offset", "must be a non-negative integer")

    return EventPageRequest(filters=filters, limit=limit, offset=int(raw_offset))


def parse_comparison_request(body: object) -> ComparisonRequest:
    def invalid(path: str, reason: str) -> ApiError:
        return ApiError(
            422,
            "invalid_request",
            "Request parameters are invalid",
            [{"parameter": path, "reason": reason}],
        )

    def record(value: object, path: str) -> dict:
        if not isinstance(value, dict):
            raise invalid(path, "must be an object")
        return value

    def only_fields(value: dict, allowed: set[str], path: str) -> None:
        if set(value) - allowed:
            raise invalid(path, "contains unknown fields")

    root = record(body, "body")
    only_fields(root, {"mode", "filters", "groups"}, "body")
    mode = root.get("mode")
    if not isinstance(mode, str) or mode not in {"live", "replay"}:
        raise invalid("mode", "must be live or replay")

    filters = record(root.get("filters", {}), "filters")
    only_fields(filters, {"min_mag"}, "filters")
    min_mag = filters.get("min_mag")
    if min_mag is not None:
        if isinstance(min_mag, bool) or not isinstance(min_mag, (int, float)):
            raise invalid("filters.min_mag", "must be a finite number or null")
        try:
            min_mag = float(min_mag)
        except OverflowError:
            raise invalid("filters.min_mag", "must be a finite number or null") from None
        if not math.isfinite(min_mag):
            raise invalid("filters.min_mag", "must be a finite number or null")

    raw_groups = root.get("groups")
    if not isinstance(raw_groups, list) or not 2 <= len(raw_groups) <= 5:
        raise invalid("groups", "must contain between 2 and 5 groups")

    groups: list[ComparisonGroup] = []
    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    for index, raw_group in enumerate(raw_groups):
        prefix = f"groups[{index}]"
        group = record(raw_group, prefix)
        only_fields(group, {"id", "label", "period", "population"}, prefix)
        group_id = group.get("id")
        label = group.get("label")
        if not isinstance(group_id, str) or not group_id.strip():
            raise invalid(f"{prefix}.id", "must be a non-empty string")
        if not isinstance(label, str) or not label.strip():
            raise invalid(f"{prefix}.label", "must be a non-empty string")
        if group_id in seen_ids:
            raise invalid(f"{prefix}.id", "must be unique")
        if label in seen_labels:
            raise invalid(f"{prefix}.label", "must be unique")
        seen_ids.add(group_id)
        seen_labels.add(label)

        period = record(group.get("period"), f"{prefix}.period")
        only_fields(period, {"start", "end"}, f"{prefix}.period")

        def parse_period_datetime(field: str) -> datetime:
            raw_value = period.get(field)
            if not isinstance(raw_value, str):
                raise invalid(f"{prefix}.period.{field}", "must be an ISO 8601 timestamp with timezone")
            try:
                parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
            except ValueError:
                raise invalid(f"{prefix}.period.{field}", "must be a valid ISO 8601 timestamp") from None
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise invalid(f"{prefix}.period.{field}", "must include a timezone offset")
            return parsed.astimezone(timezone.utc)

        start = parse_period_datetime("start")
        end = parse_period_datetime("end")
        if start >= end:
            raise invalid(f"{prefix}.period", "start must be earlier than end")

        population_data = record(group.get("population"), f"{prefix}.population")
        population_type = population_data.get("type")
        if not isinstance(population_type, str):
            raise invalid(f"{prefix}.population.type", "must be all, country, or unassigned")
        if population_type == "country":
            only_fields(population_data, {"type", "country_id"}, f"{prefix}.population")
            country_id = population_data.get("country_id")
            if not isinstance(country_id, str) or not _COUNTRY_ID.fullmatch(country_id):
                raise invalid(f"{prefix}.population.country_id", "must be a three-letter uppercase country identifier")
        elif population_type in {"all", "unassigned"}:
            only_fields(population_data, {"type"}, f"{prefix}.population")
            country_id = None
        else:
            raise invalid(f"{prefix}.population.type", "must be all, country, or unassigned")

        groups.append(
            ComparisonGroup(
                group_id=group_id,
                label=label,
                start=start,
                end=end,
                population=ComparisonPopulation(population_type, country_id),
            )
        )

    return ComparisonRequest(mode, min_mag, tuple(groups))


def iso_utc(value: datetime) -> str:
    normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z")


def epoch_milliseconds(value: datetime | None) -> int | None:
    if value is None:
        return None
    normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return int(normalized.timestamp() * 1000)
