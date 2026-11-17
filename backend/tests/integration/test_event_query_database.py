from __future__ import annotations

from datetime import datetime, timezone

import pytest

from observatorio.api.schemas import QueryFilters
from observatorio.api.queries import query_current_events
from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_event_query_uses_current_version_and_isolates_live_from_replay(api_context) -> None:
    _, factory, _ = api_context
    instant = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    await seed_api_event(
        factory,
        event_id="shared",
        event_time=instant,
        updated_at=instant,
        magnitude=2.0,
        current=False,
    )
    current_time = datetime(2026, 11, 17, 12, 30, tzinfo=timezone.utc)
    await seed_api_event(
        factory,
        event_id="shared",
        event_time=current_time,
        updated_at=current_time,
        magnitude=5.0,
    )
    await seed_api_event(
        factory,
        event_id="shared",
        mode="replay",
        event_time=current_time,
        updated_at=current_time,
        magnitude=9.0,
    )

    async with factory() as session:
        rows = await query_current_events(
            session,
            QueryFilters(
                start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
                end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
                min_mag=None,
                country_id=None,
            ),
        )

    assert len(rows) == 1
    assert rows[0].event_id == "shared"
    assert rows[0].magnitude == 5.0


@pytest.mark.asyncio
async def test_event_query_returns_successful_empty_set(api_context) -> None:
    _, factory, _ = api_context

    async with factory() as session:
        rows = await query_current_events(
            session,
            QueryFilters(
                start=datetime(2026, 11, 17, 11, tzinfo=timezone.utc),
                end=datetime(2026, 11, 17, 13, tzinfo=timezone.utc),
                min_mag=None,
                country_id=None,
            ),
        )

    assert rows == []
