from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from observatorio.api.schemas import QueryFilters
from observatorio.api.statistics import (
    build_distribution,
    build_hourly_counts,
    build_statistics,
)


def event(magnitude, depth, country="ESP", *, time=None):
    return SimpleNamespace(
        event_time=time or datetime(2026, 11, 17, 12, 15, tzinfo=timezone.utc),
        magnitude=magnitude,
        depth_km=depth,
        country_id=country,
        country_name="España" if country else None,
    )


def test_distribution_uses_only_valid_values_as_percentage_denominator() -> None:
    result = build_distribution(
        [event(3.0, 10), event(3.49, 10), event(None, None)],
        field="magnitude",
        width=0.5,
        unit="magnitude",
        missing_count=1,
    )

    assert result["valid_count"] == 2
    assert result["missing_count"] == 1
    assert result["buckets"] == [
        {
            "min_inclusive": 3.0,
            "max_exclusive": 3.5,
            "count": 2,
            "percentage": 100.0,
        }
    ]


def test_distribution_returns_null_percentage_without_valid_values() -> None:
    result = build_distribution(
        [event(None, None)],
        field="magnitude",
        width=0.5,
        unit="magnitude",
        missing_count=1,
    )

    assert result["valid_count"] == 0
    assert result["buckets"] == []


def test_hourly_counts_include_empty_utc_buckets() -> None:
    start = datetime(2026, 11, 17, 10, 30, tzinfo=timezone.utc)
    end = datetime(2026, 11, 17, 13, tzinfo=timezone.utc)

    result = build_hourly_counts(
        [event(4.0, 10, time=datetime(2026, 11, 17, 12, 5, tzinfo=timezone.utc))],
        start,
        end,
    )

    assert [bucket["count"] for bucket in result["buckets"]] == [0, 0, 1]


def test_magnitude_missing_count_is_pre_minimum_filter_population() -> None:
    filters = QueryFilters(
        start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
        end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
        min_mag=4.0,
        country_id=None,
    )
    rows = [event(4.5, 10)]

    result = build_statistics(rows, filters, magnitude_missing_count=1)

    assert result["distributions"]["magnitude"]["missing_count"] == 1
    assert result["distributions"]["magnitude"]["valid_count"] == 1
