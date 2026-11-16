"""Track the complete currently accepted source Feature for each version.

Revision ID: 0004_event_version_source
Revises: 0003_live_provenance
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_event_version_source"
down_revision = "0003_live_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_version_source",
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("original_feature", sa.JSON(), nullable=False),
        sa.Column("ingestion_run_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_event_version_source_mode"),
        sa.ForeignKeyConstraint(
            ["mode", "event_id", "updated_at"],
            ["event_version.mode", "event_version.event_id", "event_version.updated_at"],
            name="fk_event_version_source_version",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_run.run_id"],
            name="fk_event_version_source_ingestion_run",
        ),
        sa.PrimaryKeyConstraint(
            "mode",
            "event_id",
            "updated_at",
            name="pk_event_version_source",
        ),
    )


def downgrade() -> None:
    op.drop_table("event_version_source")
