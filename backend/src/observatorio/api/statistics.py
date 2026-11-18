from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observatorio.api.queries import EventRow, query_current_events
from observatorio.api.schemas import ComparisonGroup, QueryFilters, iso_utc
from observatorio.models import Country, IngestionInterval, IngestionRun

BASELINE_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
BASELINE_END = datetime(2026, 1, 1, tzinfo=timezone.utc)
BASELINE_DAYS = 365


def build_distribution(
    rows: Iterable[EventRow],
    *,
    field: str,
    width: float,
    unit: str,
    missing_count: int,
) -> dict:
    values = [
        float(value)
        for row in rows
        if (value := getattr(row, field)) is not None and math.isfinite(float(value))
    ]
    bins = Counter(math.floor(value / width) for value in values)
    valid_count = len(values)
    buckets = [
        {
            "min_inclusive": index * width,
            "max_exclusive": (index + 1) * width,
            "count": count,
            "percentage": 100.0 * count / valid_count if valid_count else None,
        }
        for index, count in sorted(bins.items())
    ]
    return {
        "unit": unit,
        "bin_width": width,
        "valid_count": valid_count,
        "missing_count": missing_count,
        "buckets": buckets,
    }


def build_hourly_counts(rows: Iterable[EventRow], start: datetime, end: datetime) -> dict:
    counts: Counter[datetime] = Counter()
    for row in rows:
        timestamp = row.event_time.replace(tzinfo=timezone.utc) if row.event_time.tzinfo is None else row.event_time.astimezone(timezone.utc)
        bucket = timestamp.replace(minute=0, second=0, microsecond=0)
        counts[bucket] += 1
    first = start.replace(minute=0, second=0, microsecond=0)
    buckets = []
    current = first
    while current < end:
        buckets.append({"start": iso_utc(current), "count": counts[current]})
        current += timedelta(hours=1)
    return {"unit": "events/hour (UTC)", "missing_count": 0, "buckets": buckets}


def _country_counts(rows: Iterable[EventRow]) -> dict:
    counts: Counter[tuple[str | None, str | None]] = Counter(
        (row.country_id, row.country_name if row.country_id is not None else "Sin país asignado")
        for row in rows
    )
    buckets = [
        {"country_id": country_id, "country_name": name, "count": count}
        for (country_id, name), count in sorted(
            counts.items(),
            key=lambda item: (item[0][0] is not None, item[0][0] or ""),
        )
    ]
    missing = sum(count for (country_id, _), count in counts.items() if country_id is None)
    return {"unit": "events", "missing_count": missing, "buckets": buckets}


def _intervals_cover_year(
    intervals: Iterable[tuple[datetime, datetime, dict]],
    *,
    min_magnitude: float | None,
) -> bool:
    normalized = sorted(
        (
            start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start.astimezone(timezone.utc),
            end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end.astimezone(timezone.utc),
        )
        for start, end, source_filters in intervals
        if isinstance(source_filters, dict)
        and "min_magnitude" in source_filters
        and (
            source_filters["min_magnitude"] is None
            or (
                isinstance(source_filters["min_magnitude"], (int, float))
                and math.isfinite(source_filters["min_magnitude"])
                and min_magnitude is not None
                and source_filters["min_magnitude"] <= min_magnitude
            )
        )
    )
    covered_until = BASELINE_START
    for start, end in normalized:
        if end <= covered_until or start > covered_until:
            continue
        covered_until = max(covered_until, end)
        if covered_until >= BASELINE_END:
            return True
    return False


def _historical_comparison(
    current_rows: list[EventRow],
    replay_rows: list[EventRow],
    interval_ranges: list[tuple[datetime, datetime, dict]],
    filters: QueryFilters,
) -> dict:
    available = _intervals_cover_year(
        interval_ranges,
        min_magnitude=filters.min_mag,
    )
    period_days = (filters.end - filters.start).total_seconds() / 86400
    current_count = len(current_rows)
    result = {
        "baseline_period": {"start": iso_utc(BASELINE_START), "end": iso_utc(BASELINE_END)},
        "baseline_days": BASELINE_DAYS,
        "baseline_available": available,
        "current_count": current_count,
        "current_period_days": period_days,
        "current_daily_average": current_count / period_days,
        "historical_daily_average": len(replay_rows) / BASELINE_DAYS if available else None,
        "unit": "events/day",
    }
    historical_average = result["historical_daily_average"]
    if historical_average is not None and historical_average > 0:
        result["daily_rate_difference"] = result["current_daily_average"] - historical_average
        result["daily_rate_ratio"] = result["current_daily_average"] / historical_average
    return result


def _covered_period(
    intervals: Iterable[tuple[datetime, datetime, dict]],
    *,
    start: datetime,
    end: datetime,
    min_magnitude: float | None,
) -> dict:
    eligible = []
    for interval_start, interval_end, source_filters in intervals:
        if not isinstance(source_filters, dict) or "min_magnitude" not in source_filters:
            continue
        requested_magnitude = source_filters["min_magnitude"]
        if requested_magnitude is not None and (
            not isinstance(requested_magnitude, (int, float))
            or not math.isfinite(requested_magnitude)
            or min_magnitude is None
            or requested_magnitude > min_magnitude
        ):
            continue
        normalized_start = interval_start.replace(tzinfo=timezone.utc) if interval_start.tzinfo is None else interval_start.astimezone(timezone.utc)
        normalized_end = interval_end.replace(tzinfo=timezone.utc) if interval_end.tzinfo is None else interval_end.astimezone(timezone.utc)
        clipped_start = max(start, normalized_start)
        clipped_end = min(end, normalized_end)
        if clipped_start < clipped_end:
            eligible.append((clipped_start, clipped_end))

    covered_seconds = 0.0
    covered_until = start
    for interval_start, interval_end in sorted(eligible):
        if interval_end <= covered_until:
            continue
        covered_seconds += (interval_end - max(interval_start, covered_until)).total_seconds()
        covered_until = interval_end
    period_seconds = (end - start).total_seconds()
    covered_days = covered_seconds / 86400
    period_days = period_seconds / 86400
    complete = covered_seconds >= period_seconds - 1e-6
    status = "complete" if complete else ("partial" if covered_seconds > 0 else "unknown")
    return {
        "status": status,
        "covered_days": round(covered_days, 10),
        "period_days": round(period_days, 10),
    }


async def build_comparison_group(
    session: AsyncSession,
    group: ComparisonGroup,
    *,
    mode: str,
    min_magnitude: float | None,
) -> dict:
    filters = QueryFilters(
        start=group.start,
        end=group.end,
        min_mag=min_magnitude,
        country_id=group.population.country_id,
    )
    country_unassigned = group.population.type == "unassigned"
    rows = await query_current_events(
        session,
        filters,
        mode=mode,
        country_unassigned=country_unassigned,
    )
    rows_without_magnitude_filter = rows if min_magnitude is None else await query_current_events(
        session,
        filters,
        mode=mode,
        include_magnitude_filter=False,
        country_unassigned=country_unassigned,
    )
    intervals = (
        await session.execute(
            select(
                IngestionInterval.interval_start,
                IngestionInterval.interval_end,
                IngestionInterval.filters,
            )
            .join(IngestionRun, IngestionRun.run_id == IngestionInterval.run_id)
            .where(
                IngestionRun.mode == mode,
                IngestionRun.outcome == "succeeded",
                IngestionInterval.status == "complete",
                IngestionInterval.interval_start < group.end,
                IngestionInterval.interval_end > group.start,
            )
        )
    ).all()
    coverage = _covered_period(
        ((start, end, source_filters) for start, end, source_filters in intervals),
        start=group.start,
        end=group.end,
        min_magnitude=min_magnitude,
    )

    observed_count = len(rows)
    unavailable_metrics: dict[str, str] = {}
    daily_rate = observed_count / coverage["period_days"] if coverage["status"] == "complete" else None
    if daily_rate is None:
        unavailable_metrics["daily_rate"] = f"coverage_{coverage['status']}"

    if coverage["status"] != "complete":
        magnitude_distribution = None
        depth_distribution = None
        unavailable_metrics["magnitude"] = f"coverage_{coverage['status']}"
        unavailable_metrics["depth_km"] = f"coverage_{coverage['status']}"
    else:
        magnitude_distribution = build_distribution(
            rows,
            field="magnitude",
            width=0.5,
            unit="magnitude",
            missing_count=sum(row.magnitude is None for row in rows_without_magnitude_filter),
        )
        depth_distribution = build_distribution(
            rows,
            field="depth_km",
            width=10,
            unit="km",
            missing_count=sum(row.depth_km is None for row in rows),
        )
        if magnitude_distribution["valid_count"] == 0:
            magnitude_distribution = None
            unavailable_metrics["magnitude"] = "no_valid_values"
        if depth_distribution["valid_count"] == 0:
            depth_distribution = None
            unavailable_metrics["depth_km"] = "no_valid_values"

    if group.population.type == "country":
        country = await session.get(Country, group.population.country_id)
        population = {
            "type": "country",
            "country_id": group.population.country_id,
            "country_name": country.country_name if country else None,
        }
    elif group.population.type == "unassigned":
        population = {
            "type": "unassigned",
            "country_id": None,
            "country_name": "Sin país asignado",
        }
    else:
        population = {"type": "all", "country_id": None, "country_name": "Todos"}

    return {
        "id": group.group_id,
        "label": group.label,
        "period": {"start": iso_utc(group.start), "end": iso_utc(group.end)},
        "population": population,
        "coverage": coverage,
        "observed_count": observed_count,
        "unavailable_metrics": unavailable_metrics,
        "daily_rate": daily_rate,
        "distributions": {
            "magnitude": magnitude_distribution,
            "depth_km": depth_distribution,
        },
    }


def build_pairwise_differences(groups: list[dict]) -> list[dict]:
    differences = []
    for first_index, first in enumerate(groups):
        for second in groups[first_index + 1:]:
            unavailable: dict[str, str] = {}
            complete = first["coverage"]["status"] == second["coverage"]["status"] == "complete"
            count_difference = second["observed_count"] - first["observed_count"] if complete else None
            if count_difference is None:
                status = first["coverage"]["status"]
                if status == "complete":
                    status = second["coverage"]["status"]
                unavailable["observed_count_difference"] = f"coverage_{status}"

            rate_difference = None
            if first["daily_rate"] is not None and second["daily_rate"] is not None:
                rate_difference = second["daily_rate"] - first["daily_rate"]
            else:
                unavailable["daily_rate_difference"] = (
                    first["unavailable_metrics"].get("daily_rate")
                    or second["unavailable_metrics"].get("daily_rate")
                    or "metric_unavailable"
                )

            percentage_differences: dict[str, list[dict] | None] = {}
            for metric in ("magnitude", "depth_km"):
                first_distribution = first["distributions"][metric]
                second_distribution = second["distributions"][metric]
                if first_distribution is None or second_distribution is None:
                    percentage_differences[metric] = None
                    unavailable[metric] = (
                        first["unavailable_metrics"].get(metric)
                        or second["unavailable_metrics"].get(metric)
                        or "metric_unavailable"
                    )
                    continue
                first_buckets = {
                    (bucket["min_inclusive"], bucket["max_exclusive"]): bucket["percentage"]
                    for bucket in first_distribution["buckets"]
                }
                second_buckets = {
                    (bucket["min_inclusive"], bucket["max_exclusive"]): bucket["percentage"]
                    for bucket in second_distribution["buckets"]
                }
                all_intervals = sorted(set(first_buckets) | set(second_buckets))
                percentage_differences[metric] = [
                    {
                        "min_inclusive": lower,
                        "max_exclusive": upper,
                        "difference": second_buckets.get((lower, upper), 0)
                        - first_buckets.get((lower, upper), 0),
                    }
                    for lower, upper in all_intervals
                ]

            differences.append(
                {
                    "first_group_id": first["id"],
                    "second_group_id": second["id"],
                    "observed_count_difference": count_difference,
                    "daily_rate_difference": rate_difference,
                    "unavailable_reasons": unavailable,
                    "distribution_percentage_point_differences": percentage_differences,
                }
            )
    return differences


def build_statistics(
    rows: list[EventRow],
    filters: QueryFilters,
    *,
    magnitude_missing_count: int | None = None,
    replay_rows: list[EventRow] | None = None,
    interval_ranges: list[tuple[datetime, datetime, dict]] | None = None,
) -> dict:
    magnitude_missing = (
        sum(row.magnitude is None for row in rows)
        if magnitude_missing_count is None
        else magnitude_missing_count
    )
    depth_missing = sum(row.depth_km is None for row in rows)
    return {
        "period": {"start": iso_utc(filters.start), "end": iso_utc(filters.end)},
        "filters": {"min_mag": filters.min_mag, "country_id": filters.country_id},
        "hourly_counts": build_hourly_counts(rows, filters.start, filters.end),
        "country_counts": _country_counts(rows),
        "distributions": {
            "magnitude": build_distribution(
                rows,
                field="magnitude",
                width=0.5,
                unit="magnitude",
                missing_count=magnitude_missing,
            ),
            "depth_km": build_distribution(
                rows,
                field="depth_km",
                width=10,
                unit="km",
                missing_count=depth_missing,
            ),
        },
        "historical_comparison": _historical_comparison(
            rows,
            replay_rows or [],
            interval_ranges or [],
            filters,
        ),
    }


async def get_statistics(session: AsyncSession, filters: QueryFilters) -> dict:
    rows = await query_current_events(session, filters)
    before_magnitude_filter = await query_current_events(
        session,
        filters,
        include_magnitude_filter=False,
    )
    historical_filters = QueryFilters(
        start=BASELINE_START,
        end=BASELINE_END,
        min_mag=filters.min_mag,
        country_id=filters.country_id,
    )
    replay_rows = await query_current_events(session, historical_filters, mode="replay")
    completed_intervals = (
        await session.execute(
            select(
                IngestionInterval.interval_start,
                IngestionInterval.interval_end,
                IngestionInterval.filters,
            )
            .join(IngestionRun, IngestionRun.run_id == IngestionInterval.run_id)
            .where(
                IngestionRun.mode == "replay",
                IngestionInterval.status == "complete",
                IngestionInterval.interval_start < BASELINE_END,
                IngestionInterval.interval_end > BASELINE_START,
            )
        )
    ).all()
    return build_statistics(
        rows,
        filters,
        magnitude_missing_count=sum(row.magnitude is None for row in before_magnitude_filter),
        replay_rows=replay_rows,
        interval_ranges=[(start, end, source_filters) for start, end, source_filters in completed_intervals],
    )
