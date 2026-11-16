"""Store verified Natural Earth country attributes.

Revision ID: 0005_country_catalog_attributes
Revises: 0004_event_version_source
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_country_catalog_attributes"
down_revision = "0004_event_version_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("country", sa.Column("name_es", sa.Text(), nullable=True))
    op.add_column("country", sa.Column("admin", sa.Text(), nullable=True))
    op.add_column("country", sa.Column("continent", sa.Text(), nullable=True))
    op.add_column("country", sa.Column("subregion", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("country", "subregion")
    op.drop_column("country", "continent")
    op.drop_column("country", "admin")
    op.drop_column("country", "name_es")
