from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    postgres_user: str = "observatorio"
    postgres_password: str = "observatorio"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "observatorio"
    kafka_bootstrap_servers: str = "kafka:9092"
    usgs_url: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    poll_seconds: int = 60
    poll_tolerance_seconds: float = 5.0
    usgs_timeout_seconds: float = 8.0
    source_archive_dir: str = "/data/source-archives"
    replay_interval_seconds: int = 2
    database_url: str | None = None

    @property
    def postgres_dsn(self) -> str:
        if self.database_url:
            return self.database_url
        if self.postgres_host:
            return (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return "sqlite+aiosqlite:///./observatorio.db"

    @property
    def sqlalchemy_database_url(self) -> str:
        return self.postgres_dsn

    def validate(self) -> None:
        if not self.postgres_host and self.database_url and self.database_url.startswith("postgresql"):
            raise ValueError("PostgreSQL host is required for PostgreSQL database URLs")
        if self.poll_seconds <= 0 or self.poll_tolerance_seconds < 0:
            raise ValueError("live polling interval and tolerance must be positive")
        if self.usgs_timeout_seconds <= 0:
            raise ValueError("USGS request timeout must be positive")
        if not self.source_archive_dir.strip():
            raise ValueError("source archive directory cannot be empty")


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    return Settings(
        postgres_user=os.getenv("POSTGRES_USER", "observatorio"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "observatorio"),
        postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "observatorio"),
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        usgs_url=os.getenv("USGS_URL", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"),
        poll_seconds=int(os.getenv("POLL_SECONDS", "60")),
        poll_tolerance_seconds=float(os.getenv("POLL_TOLERANCE_SECONDS", "5")),
        usgs_timeout_seconds=float(os.getenv("USGS_TIMEOUT_SECONDS", "8")),
        source_archive_dir=os.getenv("SOURCE_ARCHIVE_DIR", "/data/source-archives"),
        replay_interval_seconds=int(os.getenv("REPLAY_INTERVAL_SECONDS", "2")),
        database_url=database_url,
    )


settings = get_settings()
settings.validate()
