from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from observatorio.models.base import Base


class Country(Base):
    __tablename__ = "country"
    __table_args__ = (
        CheckConstraint("length(country_id) = 3", name="ck_country_id_length"),
    )

    country_id: Mapped[str] = mapped_column(String(3), primary_key=True)
    country_name: Mapped[str] = mapped_column(Text, nullable=False)


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
    records_received: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
