from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from observatorio.api import readiness
from observatorio.api.bootstrap import REQUIRED_TABLES, expected_revision
from observatorio.api.queries import latest_successful_live_ingestion, query_current_events
from observatorio.api.schemas import (
    ApiError,
    QueryFilters,
    epoch_milliseconds,
    parse_query_filters,
)
from observatorio.api.statistics import get_statistics
from observatorio.db.session import session_factory
from observatorio.logging import get_logger
from observatorio.models import Country

logger = get_logger("observatorio.api.routes")
router = APIRouter(prefix="/api")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


async def query_filters(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> QueryFilters:
    filters = parse_query_filters(request.scope.get("query_string", b""))
    if filters.country_id is not None and await session.get(Country, filters.country_id) is None:
        raise ApiError(
            422,
            "invalid_request",
            "Request parameters are invalid",
            [{"parameter": "country_id", "reason": "is not present in the country catalog"}],
        )
    return filters


def _unavailable() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "last_ingestion": None},
    )


async def _schema_is_ready(session: AsyncSession) -> bool:
    connection = await session.connection()
    tables = await connection.run_sync(lambda sync_connection: set(inspect(sync_connection).get_table_names()))
    if not REQUIRED_TABLES.issubset(tables) or "alembic_version" not in tables:
        return False
    revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
    return revision == expected_revision()


@router.get("/eventos")
async def get_events(
    filters: QueryFilters = Depends(query_filters),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    if not readiness.is_ready():
        raise ApiError(
            503,
            "dependency_unavailable",
            "A required service is unavailable",
        )
    rows = await query_current_events(session, filters)
    last_ingestion = await latest_successful_live_ingestion(session)
    generated = datetime.now(timezone.utc)
    features = []
    for row in rows:
        coordinates = [row.longitude, row.latitude]
        if row.depth_km is not None:
            coordinates.append(row.depth_km)
        features.append(
            {
                "type": "Feature",
                "id": row.event_id,
                "geometry": {"type": "Point", "coordinates": coordinates},
                "properties": {
                    "mag": row.magnitude,
                    "magType": row.mag_type,
                    "place": row.place,
                    "depth_km": row.depth_km,
                    "time": epoch_milliseconds(row.event_time),
                    "updated": epoch_milliseconds(row.updated_at),
                    "country_id": row.country_id,
                    "country_name": row.country_name,
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": epoch_milliseconds(generated),
            "last_ingestion": epoch_milliseconds(last_ingestion),
            "mode": "live",
            "count": len(features),
            "truncated": False,
        },
        "features": features,
    }


@router.get("/salud")
async def get_health(session: AsyncSession = Depends(get_db_session)) -> dict:
    if not readiness.is_ready():
        return _unavailable()
    try:
        await session.execute(text("SELECT 1"))
        if not await _schema_is_ready(session):
            return _unavailable()
        last_ingestion = await latest_successful_live_ingestion(session)
    except SQLAlchemyError as exc:
        logger.warning("API health dependency failed: %s", type(exc).__name__)
        return _unavailable()
    return {"status": "ok", "last_ingestion": epoch_milliseconds(last_ingestion)}


@router.get("/estadisticas")
async def get_event_statistics(
    filters: QueryFilters = Depends(query_filters),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    if not readiness.is_ready():
        raise ApiError(
            503,
            "dependency_unavailable",
            "A required service is unavailable",
        )
    return await get_statistics(session, filters)
