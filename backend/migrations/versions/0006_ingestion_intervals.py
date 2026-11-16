"""Add durable historical extraction interval checkpoints.

Revision ID: 0006_ingestion_intervals
Revises: 0005_country_catalog_attributes
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_ingestion_intervals"
down_revision = "0005_country_catalog_attributes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_interval",
        sa.Column("interval_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("interval_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=15), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("request_url", sa.Text(), nullable=True),
        sa.Column("http_status", sa.SmallInteger(), nullable=True),
        sa.Column("records_received", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("unique_versions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("published_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("source_archive_sha256", sa.String(length=64), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publishing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'archived', 'publishing', 'complete', 'failed')",
            name="ck_ingestion_interval_status",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_ingestion_interval_attempt_count"),
        sa.CheckConstraint("records_received >= 0", name="ck_ingestion_interval_records_received"),
        sa.CheckConstraint("unique_versions >= 0", name="ck_ingestion_interval_unique_versions"),
        sa.CheckConstraint("published_count >= 0", name="ck_ingestion_interval_published_count"),
        sa.CheckConstraint("interval_end > interval_start", name="ck_ingestion_interval_range"),
        sa.CheckConstraint("length(source_archive_sha256) = 64 OR source_archive_sha256 IS NULL", name="ck_ingestion_interval_source_archive_sha256"),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_run.run_id"], name="fk_ingestion_interval_run"),
        sa.ForeignKeyConstraint(
            ["source_archive_sha256"],
            ["source_archive.sha256"],
            name="fk_ingestion_interval_source_archive",
        ),
        sa.PrimaryKeyConstraint("interval_id", name="pk_ingestion_interval"),
        sa.UniqueConstraint(
            "run_id",
            "interval_start",
            "interval_end",
            name="uq_ingestion_interval_range",
        ),
    )


def downgrade() -> None:
    op.drop_table("ingestion_interval")
