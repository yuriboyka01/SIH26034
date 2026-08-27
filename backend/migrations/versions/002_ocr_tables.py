"""Phase 2: Add ocr_results and ocr_text_blocks tables

Revision ID: 002_ocr_tables
Revises: 001_initial_schema
Create Date: 2026-08-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002_ocr_tables"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # qualitystatus enum
    quality_enum = sa.Enum("GOOD", "FAIR", "POOR", name="qualitystatus")

    # ocr_results table
    op.create_table(
        "ocr_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "image_id",
            UUID(as_uuid=True),
            sa.ForeignKey("inspection_images.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("engine", sa.String(50), nullable=False, server_default="paddleocr"),
        sa.Column("engine_version", sa.String(50), nullable=True),
        sa.Column("full_text", sa.Text, nullable=True),
        sa.Column("processing_time_ms", sa.Integer, nullable=True),
        sa.Column("preprocessing_applied", sa.String(500), nullable=True),
        sa.Column("quality_status", quality_enum, nullable=False, server_default="GOOD"),
        sa.Column("quality_blur_score", sa.Float, nullable=True),
        sa.Column("quality_brightness_score", sa.Float, nullable=True),
        sa.Column("quality_issues", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ocr_results_image_id"), "ocr_results", ["image_id"])

    # ocr_text_blocks table
    op.create_table(
        "ocr_text_blocks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ocr_result_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ocr_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("normalized_text", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("bbox_x1", sa.Float, nullable=True),
        sa.Column("bbox_y1", sa.Float, nullable=True),
        sa.Column("bbox_x2", sa.Float, nullable=True),
        sa.Column("bbox_y2", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ocr_text_blocks_ocr_result_id"), "ocr_text_blocks", ["ocr_result_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ocr_text_blocks_ocr_result_id"), table_name="ocr_text_blocks")
    op.drop_table("ocr_text_blocks")
    op.drop_index(op.f("ix_ocr_results_image_id"), table_name="ocr_results")
    op.drop_table("ocr_results")
    sa.Enum(name="qualitystatus").drop(op.get_bind(), checkfirst=True)
