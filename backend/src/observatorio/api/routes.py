from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from observatorio.api import readiness
from observatorio.api.bootstrap import REQUIRED_TABLES, expected_revision
from observatorio.api.queries import (
    latest_successful_ingestion,
    latest_successful_live_ingestion,
    query_current_event_page,
    query_current_events,
)
from observatorio.api.schemas import (
    ApiError,
    ComparisonRequest,
    EventPageRequest,
    QueryFilters,
    epoch_milliseconds,
    parse_event_page_request,
    parse_comparison_request,
    parse_query_filters,
)
from observatorio.api.statistics import build_comparison_group, build_pairwise_differences, get_statistics
from observatorio.db.session import session_factory
from observatorio.logging import get_logger
from observatorio.models import Country

logger = get_logger("observatorio.api.routes")
router = APIRouter(prefix="/api")
_SAFE_EVENT_SOURCES = frozenset({"usgs-live", "usgs-replay"})


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


async def event_page_request(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> EventPageRequest:
    page_request = parse_event_page_request(request.scope.get("query_string", b""))
    country_id = page_request.filters.country_id
    if country_id is not None and await session.get(Country, country_id) is None:
        raise ApiError(
            422,
            "invalid_request",
            "Request parameters are invalid",
            [{"parameter": "country_id", "reason": "is not present in the country catalog"}],
        )
    return page_request


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
    page: EventPageRequest = Depends(event_page_request),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    if not readiness.is_ready():
        raise ApiError(
            503,
            "dependency_unavailable",
            "A required service is unavailable",
        )
    rows, total_count = await query_current_event_page(
        session,
        page.filters,
        limit=page.limit,
        offset=page.offset,
        mode=page.mode,
    )
    last_ingestion = await latest_successful_ingestion(session, mode=page.mode)
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
                    "traceability": {
                        "mode": row.mode,
                        "source": row.source if row.source in _SAFE_EVENT_SOURCES else None,
                        "ingested_at": epoch_milliseconds(row.ingested_at),
                        "ingestion_run_id": str(row.ingestion_run_id),
                    },
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": epoch_milliseconds(generated),
            "last_ingestion": epoch_milliseconds(last_ingestion),
            "mode": page.mode,
            "count": len(features),
            "total_count": total_count,
            "offset": page.offset,
            "limit": page.limit,
            "truncated": page.offset > 0 or len(features) < total_count,
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


@router.post("/comparaciones")
async def post_temporal_comparison(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        body = json.loads(await request.body())
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError(400, "malformed_request", "Request syntax is malformed") from None
    comparison: ComparisonRequest = parse_comparison_request(body)
    if not readiness.is_ready():
        raise ApiError(
            503,
            "dependency_unavailable",
            "A required service is unavailable",
        )

    results = []
    for index, group in enumerate(comparison.groups):
        try:
            if group.population.country_id is not None:
                country = await session.get(Country, group.population.country_id)
                if country is None:
                    raise ApiError(
                        422,
                        "invalid_request",
                        "Request parameters are invalid",
                        [{
                            "parameter": f"groups[{index}].population.country_id",
                            "reason": "is not present in the country catalog",
                        }],
                    )
            results.append(
                await build_comparison_group(
                    session,
                    group,
                    mode=comparison.mode,
                    min_magnitude=comparison.min_mag,
                )
            )
        except ApiError:
            raise
        except SQLAlchemyError as exc:
            logger.warning(
                "Temporal comparison group query failed at index %s: %s",
                index,
                type(exc).__name__,
            )
            raise ApiError(
                503,
                "dependency_unavailable",
                "A required service is unavailable",
                [{"parameter": f"groups[{index}]", "reason": "dependency_unavailable"}],
            ) from None
        except Exception as exc:
            logger.error(
                "Temporal comparison group query failed at index %s: %s",
                index,
                type(exc).__name__,
            )
            raise ApiError(
                500,
                "internal_error",
                "The request could not be completed",
                [{"parameter": f"groups[{index}]", "reason": "query_failed"}],
            ) from None

    return {
        "mode": comparison.mode,
        "filters": {"min_mag": comparison.min_mag},
        "groups": results,
        "pairwise_differences": build_pairwise_differences(results),
    }
