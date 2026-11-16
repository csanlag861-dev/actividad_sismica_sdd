"""Add source archives and acknowledged payload fingerprints.

Revision ID: 0003_live_provenance
Revises: 0002_event_current_version_fk
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_live_provenance"
down_revision = "0002_event_current_version_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_archive",
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(sha256) = 64", name="ck_source_archive_sha256_length"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_source_archive_size_bytes"),
        sa.PrimaryKeyConstraint("sha256", name="pk_source_archive"),
    )
    op.add_column(
        "ingestion_run",
        sa.Column("query_metadata", sa.JSON(), nullable=True),
    )
    op.add_column(
        "ingestion_run",
        sa.Column("source_archive_sha256", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_ingestion_run_source_archive",
        "ingestion_run",
        "source_archive",
        ["source_archive_sha256"],
        ["sha256"],
    )
    op.add_column(
        "quarantine",
        sa.Column("ingestion_run_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_quarantine_ingestion_run",
        "quarantine",
        "ingestion_run",
        ["ingestion_run_id"],
        ["run_id"],
    )
    op.create_table(
        "published_payload",
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kafka_topic", sa.Text(), nullable=False),
        sa.Column("kafka_partition", sa.Integer(), nullable=True),
        sa.Column("kafka_offset", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_published_payload_mode"),
        sa.CheckConstraint(
            "length(payload_sha256) = 64",
            name="ck_published_payload_sha256_length",
        ),
        sa.PrimaryKeyConstraint(
            "mode",
            "event_id",
            "updated_at",
            "payload_sha256",
            name="pk_published_payload",
        ),
    )


def downgrade() -> None:
    op.drop_table("published_payload")
    op.drop_constraint("fk_quarantine_ingestion_run", "quarantine", type_="foreignkey")
    op.drop_column("quarantine", "ingestion_run_id")
    op.drop_constraint("fk_ingestion_run_source_archive", "ingestion_run", type_="foreignkey")
    op.drop_column("ingestion_run", "source_archive_sha256")
    op.drop_column("ingestion_run", "query_metadata")
    op.drop_table("source_archive")
