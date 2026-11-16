from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from observatorio.db.catalog import ensure_country_catalog
from observatorio.db.session import engine, get_session
from observatorio.logging import get_logger, redact_sensitive
from observatorio.retry import retry_async

logger = get_logger("observatorio.api.bootstrap")
REQUIRED_TABLES = {
    "country",
    "calendar_date",
    "ingestion_run",
    "event_version",
    "event_current",
    "event_version_source",
    "published_version",
    "published_payload",
    "quarantine",
    "source_archive",
    "ingestion_interval",
}


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def expected_revision() -> str:
    backend_root = _backend_root()
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "migrations"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("Alembic has no head revision")
    return head


async def verify_database_ready() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # Database failures are represented as an unhealthy state.
        logger.warning("PostgreSQL readiness check failed: %s", type(exc).__name__)
        return False


async def verify_revision_applied() -> bool:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            revisions = result.scalars().all()
            if revisions != [expected_revision()]:
                return False
            tables = set(
                (
                    await conn.execute(
                        text(
                            "SELECT table_name FROM information_schema.tables "
                            "WHERE table_schema = current_schema()"
                        )
                    )
                ).scalars()
            )
            return REQUIRED_TABLES.issubset(tables)
    except Exception as exc:  # Missing or damaged schema must not be reported healthy.
        logger.warning("Alembic revision check failed: %s", type(exc).__name__)
        return False


async def _apply_migrations() -> None:
    backend_root = _backend_root()
    environment = os.environ.copy()
    src_path = str(backend_root / "src")
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_path}" if existing_path else src_path
    result = await asyncio.to_thread(
        subprocess.run,
        ["alembic", "upgrade", "head"],
        cwd=str(backend_root),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        output_lines = (result.stderr or result.stdout or "").strip().splitlines()
        detail = output_lines[-1] if output_lines else "no migration output"
        logger.error(
            "Alembic upgrade failed with exit code %s: %s",
            result.returncode,
            redact_sensitive(detail),
        )
        raise RuntimeError(f"Alembic upgrade failed with exit code {result.returncode}")


async def _seed_catalog() -> None:
    async with get_session() as session:
        await ensure_country_catalog(session)


async def bootstrap_backend() -> None:
    while True:
        try:
            await retry_async(
                _apply_migrations,
                destination="PostgreSQL Alembic migrations",
                max_attempts=5,
                base_delay=1.0,
                max_delay=10.0,
            )
            await retry_async(
                _seed_catalog,
                destination="PostgreSQL Natural Earth country catalog",
                max_attempts=5,
                base_delay=1.0,
                max_delay=10.0,
            )
        except Exception as exc:
            logger.error("Backend bootstrap failed; retrying: %s", type(exc).__name__)
            await asyncio.sleep(5)
            continue

        if await verify_database_ready() and await verify_revision_applied():
            logger.info("Backend bootstrap is healthy at Alembic revision %s", expected_revision())
            await asyncio.sleep(10)
        else:
            logger.warning("Database schema is not ready; retrying bootstrap")
            await asyncio.sleep(5)


def main() -> None:
    asyncio.run(bootstrap_backend())


if __name__ == "__main__":
    main()
