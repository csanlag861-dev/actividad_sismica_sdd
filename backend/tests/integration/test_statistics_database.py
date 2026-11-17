from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from observatorio.api.schemas import QueryFilters
from observatorio.api.statistics import get_statistics
from observatorio.models import IngestionInterval, IngestionRun
from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_statistics_aggregate_complete_current_set_not_response_sample(api_context) -> None:
    _, factory, _ = api_context
    for event_id, magnitude in (("one", 3.0), ("two", 4.0), ("three", 5.0)):
        await seed_api_event(
            factory,
            event_id=event_id,
            event_time=datetime(2026, 11, 17, 12, tzinfo=timezone.utc),
            magnitude=magnitude,
        )
    filters = QueryFilters(
        start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
        end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
        min_mag=None,
        country_id=None,
    )

    async with factory() as session:
        result = await get_statistics(session, filters)

    assert result["distributions"]["magnitude"]["valid_count"] == 3
    assert sum(bucket["count"] for bucket in result["country_counts"]["buckets"]) == 3
    assert result["historical_comparison"]["baseline_available"] is False
    assert result["historical_comparison"]["historical_daily_average"] is None


@pytest.mark.asyncio
async def test_historical_baseline_requires_complete_year_coverage_and_counts_zero_days(api_context) -> None:
    _, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="historic",
        mode="replay",
        event_time=datetime(2025, 6, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )
    async with factory() as session:
        replay_run = await session.scalar(
            select(IngestionRun).where(IngestionRun.mode == "replay")
        )
        session.add(
            IngestionInterval(
                run_id=replay_run.run_id,
                interval_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                interval_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
                filters={"min_magnitude": None, "event_type": "earthquake"},
                status="complete",
                records_received=1,
                unique_versions=1,
                published_count=1,
            )
        )
        await session.commit()

    filters = QueryFilters(
        start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
        end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
        min_mag=None,
        country_id=None,
    )
    async with factory() as session:
        result = await get_statistics(session, filters)

    comparison = result["historical_comparison"]
    assert comparison["baseline_available"] is True
    assert comparison["historical_daily_average"] == pytest.approx(1 / 365)
    assert "daily_rate_difference" in comparison
    assert "daily_rate_ratio" in comparison


@pytest.mark.asyncio
async def test_zero_historical_baseline_omits_rate_ratio(api_context) -> None:
    _, factory, _ = api_context
    await seed_api_event(
        factory,
        event_id="covered-zero",
        mode="replay",
        event_time=datetime(2025, 6, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        current=False,
    )
    async with factory() as session:
        replay_run = await session.scalar(
            select(IngestionRun).where(IngestionRun.mode == "replay")
        )
        session.add(
            IngestionInterval(
                run_id=replay_run.run_id,
                interval_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                interval_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
                filters={"min_magnitude": None, "event_type": "earthquake"},
                status="complete",
            )
        )
        await session.commit()

    filters = QueryFilters(
        start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
        end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
        min_mag=None,
        country_id=None,
    )
    async with factory() as session:
        result = await get_statistics(session, filters)

    comparison = result["historical_comparison"]
    assert comparison["baseline_available"] is True
    assert comparison["historical_daily_average"] == 0
    assert "daily_rate_difference" not in comparison
    assert "daily_rate_ratio" not in comparison


@pytest.mark.asyncio
async def test_baseline_requires_replay_minimum_to_cover_requested_population(api_context) -> None:
    _, factory, _ = api_context
    async with factory() as session:
        run = IngestionRun(
            run_id=uuid4(),
            mode="replay",
            source="usgs-replay",
            started_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            outcome="succeeded",
            request_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
            request_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
            records_received=0,
        )
        session.add(run)
        await session.flush()
        session.add(
            IngestionInterval(
                run_id=run.run_id,
                interval_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                interval_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
                filters={"min_magnitude": 4.0, "event_type": "earthquake"},
                status="complete",
            )
        )
        await session.commit()

    for min_magnitude, expected_available in ((3.9, False), (4.0, True), (5.0, True), (None, False)):
        filters = QueryFilters(
            start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
            end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
            min_mag=min_magnitude,
            country_id=None,
        )
        async with factory() as session:
            result = await get_statistics(session, filters)

        comparison = result["historical_comparison"]
        assert comparison["baseline_available"] is expected_available
        assert (comparison["historical_daily_average"] is None) is not expected_available
