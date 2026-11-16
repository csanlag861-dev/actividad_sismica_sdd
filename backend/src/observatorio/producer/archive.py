from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observatorio.config import settings
from observatorio.db.session import session_factory
from observatorio.logging import get_logger
from observatorio.models import (
    EventVersion,
    EventVersionSource,
    IngestionInterval,
    IngestionRun,
    Quarantine,
    SourceArchive,
)

logger = get_logger("observatorio.producer.archive")


@dataclass(frozen=True)
class ArchivedResponse:
    sha256: str
    path: Path
    size_bytes: int


def _write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_hash != hashlib.sha256(content).hexdigest():
            raise OSError(f"archive path contains different content: {path}")
        return

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".archive-", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


async def archive_response(
    content: bytes,
    *,
    source: str,
    directory: Path | str | None = None,
    ingestion_run_id: UUID | None = None,
    ingestion_interval_id: int | None = None,
    session_factory_override: async_sessionmaker[AsyncSession] | None = None,
) -> ArchivedResponse:
    if not isinstance(content, bytes):
        raise TypeError("source response must be archived as its original bytes")
    if not source.strip():
        raise ValueError("archive source cannot be empty")

    digest = hashlib.sha256(content).hexdigest()
    root = Path(directory or settings.source_archive_dir)
    path = root / digest[:2] / f"{digest}.geojson"
    await asyncio.to_thread(_write_atomically, path, content)

    factory = session_factory_override or session_factory
    async with factory() as session:
        async with session.begin():
            archive = await session.get(SourceArchive, digest)
            if archive is None:
                session.add(
                    SourceArchive(
                        sha256=digest,
                        storage_path=str(path),
                        size_bytes=len(content),
                        source=source,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            else:
                archive.storage_path = str(path)
                archive.size_bytes = len(content)
                archive.source = source
                archive.deleted_at = None
            if ingestion_run_id is not None:
                run = await session.get(IngestionRun, ingestion_run_id)
                if run is None:
                    raise ValueError(f"ingestion run does not exist: {ingestion_run_id}")
                run.source_archive_sha256 = digest
            if ingestion_interval_id is not None:
                interval = await session.get(IngestionInterval, ingestion_interval_id)
                if interval is None:
                    raise ValueError(f"ingestion interval does not exist: {ingestion_interval_id}")
                interval.source_archive_sha256 = digest

    return ArchivedResponse(sha256=digest, path=path, size_bytes=len(content))


async def cleanup_unreferenced_archives(
    *,
    session_factory_override: async_sessionmaker[AsyncSession] | None = None,
) -> list[str]:
    """Remove only succeeded, empty-response archives with no processed dependents."""
    factory = session_factory_override or session_factory
    removed: list[str] = []
    async with factory() as session:
        async with session.begin():
            archives = (
                await session.scalars(
                    select(SourceArchive).where(SourceArchive.deleted_at.is_(None))
                )
            ).all()
            for archive in archives:
                direct_runs = (
                    await session.scalars(
                        select(IngestionRun).where(
                            IngestionRun.source_archive_sha256 == archive.sha256
                        )
                    )
                ).all()
                intervals = (
                    await session.scalars(
                        select(IngestionInterval).where(
                            IngestionInterval.source_archive_sha256 == archive.sha256
                        )
                    )
                ).all()
                run_ids = {run.run_id for run in direct_runs}
                run_ids.update(interval.run_id for interval in intervals)
                if not run_ids:
                    continue
                runs = (
                    await session.scalars(
                        select(IngestionRun).where(IngestionRun.run_id.in_(run_ids))
                    )
                ).all()
                if (
                    any(run.outcome != "succeeded" or run.records_received != 0 for run in runs)
                    or any(
                        interval.status != "complete" or interval.records_received != 0
                        for interval in intervals
                    )
                ):
                    continue
                has_versions = await session.scalar(
                    select(EventVersion.event_id)
                    .where(EventVersion.ingestion_run_id.in_(run_ids))
                    .limit(1)
                )
                has_version_sources = await session.scalar(
                    select(EventVersionSource.mode)
                    .where(EventVersionSource.ingestion_run_id.in_(run_ids))
                    .limit(1)
                )
                has_quarantines = await session.scalar(
                    select(Quarantine.quarantine_id)
                    .where(Quarantine.ingestion_run_id.in_(run_ids))
                    .limit(1)
                )
                if (
                    has_versions is not None
                    or has_version_sources is not None
                    or has_quarantines is not None
                ):
                    continue

                Path(archive.storage_path).unlink(missing_ok=True)
                archive.deleted_at = datetime.now(timezone.utc)
                removed.append(archive.sha256)
    if removed:
        logger.info("Removed %s unreferenced empty source archives", len(removed))
    return removed


async def main_async() -> None:
    removed = await cleanup_unreferenced_archives()
    logger.info("Archive cleanup completed; %s files were removed", len(removed))


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
