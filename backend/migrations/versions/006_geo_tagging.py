"""Geo-tagging: add establishment_name, latitude, longitude to inspections

Revision ID: 006_geo_tagging
Revises: 005_rule_engine_v2
Create Date: 2026-09-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_geo_tagging'
down_revision: Union[str, None] = '005_rule_engine_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive, nullable columns — safe for existing rows. Geo-tagging is
    # captured client-side via the browser Geolocation API and is optional,
    # so existing inspections simply have NULL here.
    op.add_column('inspections', sa.Column('establishment_name', sa.String(500), nullable=True))
    op.add_column('inspections', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('inspections', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('inspections', 'longitude')
    op.drop_column('inspections', 'latitude')
    op.drop_column('inspections', 'establishment_name')
