"""Initial schema: users, inspections, inspection_images

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-08-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_role_enum = sa.Enum("ADMIN", "INSPECTOR", name="userrole")
    inspection_status_enum = sa.Enum(
        "CREATED", "IMAGES_UPLOADED", "PROCESSING", "COMPLETED", "NEEDS_REVIEW",
        name="inspectionstatus",
    )
    image_type_enum = sa.Enum("FRONT", "BACK", "SIDE", "OTHER", name="imagetype")

    # Enum creation is automatically handled by op.create_table in PostgreSQL

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False, server_default="INSPECTOR"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Inspections table
    op.create_table(
        "inspections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_number", sa.String(50), unique=True, nullable=False),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(255), nullable=False),
        sa.Column("status", inspection_status_enum, nullable=False, server_default="CREATED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inspections_inspection_number", "inspections", ["inspection_number"])

    # Inspection images table
    op.create_table(
        "inspection_images",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "inspection_id",
            UUID(as_uuid=True),
            sa.ForeignKey("inspections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("stored_filename", sa.String(255), unique=True, nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("image_type", image_type_enum, nullable=False, server_default="OTHER"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inspection_images_inspection_id", "inspection_images", ["inspection_id"])


def downgrade() -> None:
    op.drop_table("inspection_images")
    op.drop_table("inspections")
    op.drop_table("users")

    # Drop enum types
    sa.Enum(name="imagetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="inspectionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
