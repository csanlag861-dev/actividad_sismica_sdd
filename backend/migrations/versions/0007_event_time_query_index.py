"""Index current-event time-window queries.

Revision ID: 0007_event_time_query_index
Revises: 0006_ingestion_intervals
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_event_time_query_index"
down_revision = "0006_ingestion_intervals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_event_version_mode_event_time",
        "event_version",
        ["mode", sa.text("event_time DESC"), "event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_version_mode_event_time", table_name="event_version")
