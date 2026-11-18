from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observatorio.api.schemas import QueryFilters
from observatorio.models import Country, EventCurrent, EventVersion, IngestionRun


@dataclass(frozen=True)
class EventRow:
    mode: str
    event_id: str
    updated_at: datetime
    source: str
    ingested_at: datetime
    ingestion_run_id: UUID
    event_time: datetime
    magnitude: float | None
    mag_type: str | None
    place: str | None
    longitude: float
    latitude: float
    depth_km: float | None
    country_id: str | None
    country_name: str | None


def _event_statement(
    filters: QueryFilters,
    *,
    mode: str,
    include_magnitude_filter: bool = True,
    country_unassigned: bool = False,
):
    statement = (
        select(EventVersion, Country.country_name)
        .join(
            EventCurrent,
            and_(
                EventCurrent.mode == EventVersion.mode,
                EventCurrent.event_id == EventVersion.event_id,
                EventCurrent.current_updated_at == EventVersion.updated_at,
            ),
        )
        .outerjoin(Country, Country.country_id == EventVersion.country_id)
        .where(
            EventCurrent.mode == mode,
            EventVersion.event_time >= filters.start,
            EventVersion.event_time < filters.end,
        )
    )
    if include_magnitude_filter and filters.min_mag is not None:
        statement = statement.where(EventVersion.magnitude >= filters.min_mag)
    if filters.country_id is not None:
        statement = statement.where(EventVersion.country_id == filters.country_id)
    elif country_unassigned:
        statement = statement.where(EventVersion.country_id.is_(None))
    return statement.order_by(EventVersion.event_time.desc(), EventVersion.event_id.asc())


async def _rows(session: AsyncSession, statement) -> list[EventRow]:
    records = (await session.execute(statement)).all()
    return [
        EventRow(
            mode=version.mode,
            event_id=version.event_id,
            updated_at=version.updated_at,
            source=version.source,
            ingested_at=version.ingested_at,
            ingestion_run_id=version.ingestion_run_id,
            event_time=version.event_time,
            magnitude=float(version.magnitude) if version.magnitude is not None else None,
            mag_type=version.mag_type,
            place=version.place,
            longitude=float(version.longitude),
            latitude=float(version.latitude),
            depth_km=float(version.depth_km) if version.depth_km is not None else None,
            country_id=version.country_id,
            country_name=country_name,
        )
        for version, country_name in records
    ]


async def query_current_events(
    session: AsyncSession,
    filters: QueryFilters,
    *,
    mode: str = "live",
    include_magnitude_filter: bool = True,
    country_unassigned: bool = False,
) -> list[EventRow]:
    return await _rows(
        session,
        _event_statement(
            filters,
            mode=mode,
            include_magnitude_filter=include_magnitude_filter,
            country_unassigned=country_unassigned,
        ),
    )


async def query_current_event_page(
    session: AsyncSession,
    filters: QueryFilters,
    *,
    limit: int,
    offset: int,
    mode: str = "live",
) -> tuple[list[EventRow], int]:
    statement = _event_statement(filters, mode=mode)
    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total_count = int(await session.scalar(count_statement) or 0)
    rows = await _rows(session, statement.limit(limit).offset(offset))
    return rows, total_count


async def latest_successful_ingestion(
    session: AsyncSession,
    *,
    mode: str = "live",
) -> datetime | None:
    ingestion_time = (
        IngestionRun.request_end
        if mode == "live"
        else IngestionRun.finished_at
    )
    conditions = [
        IngestionRun.mode == mode,
        IngestionRun.outcome == "succeeded",
        ingestion_time.is_not(None),
    ]
    if mode == "live":
        conditions.append(IngestionRun.source == "usgs-live")
    result = await session.scalar(
        select(func.max(ingestion_time)).where(*conditions)
    )
    return result


async def latest_successful_live_ingestion(session: AsyncSession) -> datetime | None:
    return await latest_successful_ingestion(session, mode="live")
