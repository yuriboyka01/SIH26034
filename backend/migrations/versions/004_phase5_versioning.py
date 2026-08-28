"""Phase 5: Add versioning columns to compliance_reports

Revision ID: 004_phase5_versioning
Revises: c8ec16622252
Create Date: 2026-08-28 06:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_phase5_versioning'
down_revision: Union[str, None] = 'c8ec16622252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable columns first
    op.add_column('compliance_reports', sa.Column('engine_version', sa.String(50), nullable=True))
    op.add_column('compliance_reports', sa.Column('ruleset_version', sa.String(50), nullable=True))

    # Backfill existing rows with known defaults so they are not NULL
    op.execute("UPDATE compliance_reports SET engine_version = '1.0.0' WHERE engine_version IS NULL")
    op.execute("UPDATE compliance_reports SET ruleset_version = 'LM-2011-v1' WHERE ruleset_version IS NULL")


def downgrade() -> None:
    op.drop_column('compliance_reports', 'ruleset_version')
    op.drop_column('compliance_reports', 'engine_version')
