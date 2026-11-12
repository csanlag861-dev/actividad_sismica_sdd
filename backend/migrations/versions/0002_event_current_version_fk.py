"""Ensure current event rows reference an observed version.

Revision ID: 0002_event_current_version_fk
Revises: 0001_initial_schema
"""

from __future__ import annotations

from alembic import op

revision = "0002_event_current_version_fk"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_event_current_version",
        "event_current",
        "event_version",
        ["mode", "event_id", "current_updated_at"],
        ["mode", "event_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_event_current_version", "event_current", type_="foreignkey")
