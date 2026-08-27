"""Phase 3: Add product_info table for structured extraction results

Revision ID: 003_product_info
Revises: 002_ocr_tables
Create Date: 2026-08-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003_product_info"
down_revision: Union[str, None] = "002_ocr_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_info",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ocr_result_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ocr_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Extracted fields (NULL = not detected)
        sa.Column("product_name", sa.String(500), nullable=True),
        sa.Column("brand_name", sa.String(255), nullable=True),
        sa.Column("manufacturer", sa.Text, nullable=True),
        sa.Column("net_quantity", sa.String(200), nullable=True),
        sa.Column("mrp", sa.String(100), nullable=True),
        sa.Column("manufacturing_date", sa.String(100), nullable=True),
        sa.Column("expiry_date", sa.String(100), nullable=True),
        sa.Column("batch_number", sa.String(200), nullable=True),
        sa.Column("country_of_origin", sa.String(200), nullable=True),
        sa.Column("ingredients", sa.Text, nullable=True),
        sa.Column("license_number", sa.String(300), nullable=True),
        sa.Column("customer_care", sa.String(200), nullable=True),
        sa.Column("warnings", sa.Text, nullable=True),
        # Full evidence-linked fields as JSON
        sa.Column("fields_json", sa.Text, nullable=True),
        # Metadata
        sa.Column("total_blocks_processed", sa.Integer, nullable=True),
        sa.Column("extraction_version", sa.String(20), nullable=True, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_product_info_ocr_result_id"), "product_info", ["ocr_result_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_product_info_ocr_result_id"), table_name="product_info")
    op.drop_table("product_info")
