from __future__ import annotations

from datetime import datetime, timezone

import pytest

from observatorio.api.schemas import ApiError, parse_event_page_request, parse_query_filters


def test_query_filters_normalize_offsets_and_apply_defaults() -> None:
    now = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)

    filters = parse_query_filters(
        b"start=2026-11-17T13%3A00%3A00%2B01%3A00&end=2026-11-17T14%3A00%3A00%2B01%3A00&min_mag=4.5&country_id=ESP",
        now=now,
    )

    assert filters.start == datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    assert filters.end == datetime(2026, 11, 17, 13, tzinfo=timezone.utc)
    assert filters.min_mag == 4.5
    assert filters.country_id == "ESP"


@pytest.mark.parametrize(
    "query",
    [
        b"unknown=value",
        b"min_mag=nan",
        b"start=2026-11-17T12%3A00%3A00",
        b"start=not-a-date",
        b"start=2026-11-18T00%3A00%3A00Z&end=2026-11-17T00%3A00%3A00Z",
        b"country_id=es",
        b"start=%ZZ",
        b"start=2026-11-17T00%3A00%3A00Z&start=2026-11-18T00%3A00%3A00Z",
    ],
)
def test_query_filters_reject_invalid_or_ambiguous_values(query: bytes) -> None:
    with pytest.raises(ApiError):
        parse_query_filters(query, now=datetime(2026, 11, 17, tzinfo=timezone.utc))


def test_unknown_query_parameter_name_is_not_reflected() -> None:
    with pytest.raises(ApiError) as error_info:
        parse_query_filters(
            b"x" * 10_000 + b"=attacker-controlled",
            now=datetime(2026, 11, 17, tzinfo=timezone.utc),
        )
    error = error_info.value

    assert error.details == [
        {"parameter": "query", "reason": "contains an unknown query parameter"}
    ]


def test_event_page_request_applies_defaults_without_changing_statistics_filters() -> None:
    now = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    page = parse_event_page_request(b"", now=now)

    assert page.limit == 25
    assert page.offset == 0
    assert page.mode == "live"
    assert page.filters.start == datetime(2026, 11, 16, 12, tzinfo=timezone.utc)
    with pytest.raises(ApiError):
        parse_query_filters(b"limit=25", now=now)


@pytest.mark.parametrize("limit", [b"24", b"101", b"25.0", b"nan", b""])
def test_event_page_request_rejects_invalid_page_sizes(limit: bytes) -> None:
    with pytest.raises(ApiError) as error_info:
        parse_event_page_request(b"limit=" + limit)
    assert error_info.value.details[0]["parameter"] == "limit"


@pytest.mark.parametrize("offset", [b"-1", b"1.2", b"abc", b""])
def test_event_page_request_rejects_invalid_offsets(offset: bytes) -> None:
    with pytest.raises(ApiError) as error_info:
        parse_event_page_request(b"offset=" + offset)
    assert error_info.value.details[0]["parameter"] == "offset"


@pytest.mark.parametrize("limit", [25, 50, 100])
def test_event_page_request_accepts_supported_sizes(limit: int) -> None:
    page = parse_event_page_request(f"limit={limit}&offset=75".encode())
    assert page.limit == limit
    assert page.offset == 75


def test_event_page_request_accepts_replay_mode() -> None:
    page = parse_event_page_request(b"mode=replay")

    assert page.mode == "replay"


def test_event_page_request_rejects_unknown_mode() -> None:
    with pytest.raises(ApiError) as error_info:
        parse_event_page_request(b"mode=archive")

    assert error_info.value.details[0]["parameter"] == "mode"
