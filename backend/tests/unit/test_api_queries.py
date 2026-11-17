from __future__ import annotations

from datetime import datetime, timezone

import pytest

from observatorio.api.schemas import ApiError, parse_query_filters


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
