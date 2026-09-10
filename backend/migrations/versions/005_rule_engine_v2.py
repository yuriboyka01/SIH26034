"""Rule engine v2: add category, confidence, remediation to compliance_rule_results

Revision ID: 005_rule_engine_v2
Revises: 004_phase5_versioning
Create Date: 2026-09-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_rule_engine_v2'
down_revision: Union[str, None] = '004_phase5_versioning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive, nullable columns — safe for existing rows.
    op.add_column('compliance_rule_results', sa.Column('category', sa.String(50), nullable=True))
    op.add_column('compliance_rule_results', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('compliance_rule_results', sa.Column('remediation', sa.Text(), nullable=True))

    # Backfill existing rows with a generic category so old reports still group sensibly.
    op.execute("UPDATE compliance_rule_results SET category = 'MANDATORY_DECLARATIONS' WHERE category IS NULL")


def downgrade() -> None:
    op.drop_column('compliance_rule_results', 'remediation')
    op.drop_column('compliance_rule_results', 'confidence')
    op.drop_column('compliance_rule_results', 'category')
