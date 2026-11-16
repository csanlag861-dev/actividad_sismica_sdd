from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from observatorio.models.base import Base


class PublishedVersion(Base):
    __tablename__ = "published_version"
    __table_args__ = (
        PrimaryKeyConstraint("mode", "event_id", "updated_at", name="pk_published_version"),
        CheckConstraint("mode IN ('live', 'replay')", name="ck_published_version_mode"),
    )

    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kafka_topic: Mapped[str] = mapped_column(Text, nullable=False)
    kafka_partition: Mapped[int | None] = mapped_column(nullable=True)
    kafka_offset: Mapped[int | None] = mapped_column(nullable=True)


class PublishedPayload(Base):
    __tablename__ = "published_payload"
    __table_args__ = (
        PrimaryKeyConstraint(
            "mode",
            "event_id",
            "updated_at",
            "payload_sha256",
            name="pk_published_payload",
        ),
        CheckConstraint("mode IN ('live', 'replay')", name="ck_published_payload_mode"),
        CheckConstraint(
            "length(payload_sha256) = 64",
            name="ck_published_payload_sha256_length",
        ),
    )

    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kafka_topic: Mapped[str] = mapped_column(Text, nullable=False)
    kafka_partition: Mapped[int | None] = mapped_column(nullable=True)
    kafka_offset: Mapped[int | None] = mapped_column(nullable=True)
