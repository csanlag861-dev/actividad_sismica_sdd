"""Initial schema for the observatorio backend.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "country",
        sa.Column("country_id", sa.String(length=3), nullable=False),
        sa.Column("country_name", sa.Text(), nullable=False),
        sa.CheckConstraint("length(country_id) = 3", name="ck_country_id_length"),
        sa.PrimaryKeyConstraint("country_id", name="pk_country"),
    )
    op.create_table(
        "calendar_date",
        sa.Column("date_utc", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("date_utc", name="pk_calendar_date"),
    )
    op.create_table(
        "ingestion_run",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=15), nullable=False),
        sa.Column("request_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status", sa.SmallInteger(), nullable=True),
        sa.Column("records_received", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_ingestion_run_mode"),
        sa.CheckConstraint("outcome IN ('running', 'succeeded', 'failed')", name="ck_ingestion_run_outcome"),
        sa.PrimaryKeyConstraint("run_id", name="pk_ingestion_run"),
    )
    op.create_table(
        "event_version",
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("magnitude", sa.Numeric(), nullable=True),
        sa.Column("mag_type", sa.Text(), nullable=True),
        sa.Column("place", sa.Text(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("depth_km", sa.Float(), nullable=True),
        sa.Column("country_id", sa.String(length=3), nullable=True),
        sa.Column("date_utc", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingestion_run_id", sa.Uuid(), nullable=False),
        sa.Column("original_payload", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=False),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_event_version_mode"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_event_version_longitude_range"),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_event_version_latitude_range"),
        sa.ForeignKeyConstraint(["country_id"], ["country.country_id"], name="fk_event_version_country"),
        sa.ForeignKeyConstraint(["date_utc"], ["calendar_date.date_utc"], name="fk_event_version_calendar_date"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], name="fk_event_version_ingestion_run"),
        sa.PrimaryKeyConstraint("mode", "event_id", "updated_at", name="pk_event_version"),
    )
    op.create_table(
        "event_current",
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("current_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_event_current_mode"),
        sa.PrimaryKeyConstraint("mode", "event_id", name="pk_event_current"),
    )
    op.create_table(
        "published_version",
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kafka_topic", sa.Text(), nullable=False),
        sa.Column("kafka_partition", sa.Integer(), nullable=True),
        sa.Column("kafka_offset", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_published_version_mode"),
        sa.PrimaryKeyConstraint("mode", "event_id", "updated_at", name="pk_published_version"),
    )
    op.create_table(
        "quarantine",
        sa.Column("quarantine_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_code", sa.Text(), nullable=False),
        sa.Column("reason_detail", sa.Text(), nullable=False),
        sa.Column("kafka_topic", sa.Text(), nullable=False),
        sa.Column("kafka_partition", sa.Integer(), nullable=False),
        sa.Column("kafka_offset", sa.BigInteger(), nullable=False),
        sa.Column("raw_message", sa.LargeBinary(), nullable=False),
        sa.Column("parsed_payload", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=True),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_quarantine_mode"),
        sa.PrimaryKeyConstraint("quarantine_id", name="pk_quarantine"),
        sa.UniqueConstraint("kafka_topic", "kafka_partition", "kafka_offset", name="uq_quarantine_kafka_position"),
    )
    op.create_index("ix_event_version_event_id", "event_version", ["event_id"], unique=False)
    op.create_index("ix_event_version_date_utc", "event_version", ["date_utc"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_version_date_utc", table_name="event_version")
    op.drop_index("ix_event_version_event_id", table_name="event_version")
    op.drop_table("quarantine")
    op.drop_table("published_version")
    op.drop_table("event_current")
    op.drop_table("event_version")
    op.drop_table("ingestion_run")
    op.drop_table("calendar_date")
    op.drop_table("country")
