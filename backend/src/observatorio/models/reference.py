from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from observatorio.models.base import Base


class Country(Base):
    __tablename__ = "country"
    __table_args__ = (
        CheckConstraint("length(country_id) = 3", name="ck_country_id_length"),
    )

    country_id: Mapped[str] = mapped_column(String(3), primary_key=True)
    country_name: Mapped[str] = mapped_column(Text, nullable=False)
    name_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin: Mapped[str | None] = mapped_column(Text, nullable=True)
    continent: Mapped[str | None] = mapped_column(Text, nullable=True)
    subregion: Mapped[str | None] = mapped_column(Text, nullable=True)


class CalendarDate(Base):
    __tablename__ = "calendar_date"

    date_utc: Mapped[date] = mapped_column(Date, primary_key=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_run"
    __table_args__ = (
        CheckConstraint("mode IN ('live', 'replay')", name="ck_ingestion_run_mode"),
        CheckConstraint("outcome IN ('running', 'succeeded', 'failed')", name="ck_ingestion_run_outcome"),
    )

    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str] = mapped_column(String(15), nullable=False)
    request_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    request_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    http_status: Mapped[int | None] = mapped_column(nullable=True)
    query_metadata: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
    source_archive_sha256: Mapped[str | None] = mapped_column(
        ForeignKey("source_archive.sha256"),
        nullable=True,
    )
    records_received: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceArchive(Base):
    __tablename__ = "source_archive"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_source_archive_sha256_length"),
        CheckConstraint("size_bytes >= 0", name="ck_source_archive_size_bytes"),
    )

    sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionInterval(Base):
    __tablename__ = "ingestion_interval"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "interval_start",
            "interval_end",
            name="uq_ingestion_interval_range",
        ),
        PrimaryKeyConstraint("interval_id", name="pk_ingestion_interval"),
        CheckConstraint(
            "status IN ('pending', 'archived', 'publishing', 'complete', 'failed')",
            name="ck_ingestion_interval_status",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_ingestion_interval_attempt_count"),
        CheckConstraint("records_received >= 0", name="ck_ingestion_interval_records_received"),
        CheckConstraint("unique_versions >= 0", name="ck_ingestion_interval_unique_versions"),
        CheckConstraint("published_count >= 0", name="ck_ingestion_interval_published_count"),
        CheckConstraint("interval_end > interval_start", name="ck_ingestion_interval_range"),
        CheckConstraint(
            "length(source_archive_sha256) = 64 OR source_archive_sha256 IS NULL",
            name="ck_ingestion_interval_source_archive_sha256",
        ),
    )

    interval_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("ingestion_run.run_id"), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, server_default=text("'pending'"))
    attempt_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    request_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    http_status: Mapped[int | None] = mapped_column(nullable=True)
    records_received: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    unique_versions: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    published_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    source_archive_sha256: Mapped[str | None] = mapped_column(
        ForeignKey("source_archive.sha256"),
        nullable=True,
    )
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publishing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
