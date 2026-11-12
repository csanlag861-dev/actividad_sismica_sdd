from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, LargeBinary, PrimaryKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from observatorio.models.base import Base


class Quarantine(Base):
    __tablename__ = "quarantine"
    __table_args__ = (
        PrimaryKeyConstraint("quarantine_id", name="pk_quarantine"),
        UniqueConstraint("kafka_topic", "kafka_partition", "kafka_offset", name="uq_quarantine_kafka_position"),
        CheckConstraint("mode IN ('live', 'replay')", name="ck_quarantine_mode"),
    )

    quarantine_id: Mapped[UUID] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    event_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False)
    reason_detail: Mapped[str] = mapped_column(Text, nullable=False)
    kafka_topic: Mapped[str] = mapped_column(Text, nullable=False)
    kafka_partition: Mapped[int] = mapped_column(nullable=False)
    kafka_offset: Mapped[int] = mapped_column(nullable=False)
    raw_message: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    parsed_payload: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
