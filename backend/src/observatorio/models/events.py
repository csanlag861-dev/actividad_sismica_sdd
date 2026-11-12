from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Numeric, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from observatorio.models.base import Base

if TYPE_CHECKING:
    from observatorio.models.reference import CalendarDate, Country, IngestionRun


class EventVersion(Base):
    __tablename__ = "event_version"
    __table_args__ = (
        PrimaryKeyConstraint("mode", "event_id", "updated_at", name="pk_event_version"),
        CheckConstraint("mode IN ('live', 'replay')", name="ck_event_version_mode"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_event_version_longitude_range"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_event_version_latitude_range"),
    )

    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    magnitude: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    mag_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    place: Mapped[str | None] = mapped_column(Text, nullable=True)
    longitude: Mapped[float] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    depth_km: Mapped[float | None] = mapped_column(nullable=True)
    country_id: Mapped[str | None] = mapped_column(ForeignKey("country.country_id"), nullable=True)
    date_utc: Mapped[date] = mapped_column(ForeignKey("calendar_date.date_utc"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey("ingestion_run.run_id"), nullable=False)
    original_payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)

    country: Mapped[Country | None] = relationship()
    calendar_date: Mapped[CalendarDate] = relationship()
    run: Mapped[IngestionRun] = relationship()


class EventCurrent(Base):
    __tablename__ = "event_current"
    __table_args__ = (
        PrimaryKeyConstraint("mode", "event_id", name="pk_event_current"),
        CheckConstraint("mode IN ('live', 'replay')", name="ck_event_current_mode"),
        ForeignKeyConstraint(
            ["mode", "event_id", "current_updated_at"],
            ["event_version.mode", "event_version.event_id", "event_version.updated_at"],
            name="fk_event_current_version",
        ),
    )

    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    current_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
