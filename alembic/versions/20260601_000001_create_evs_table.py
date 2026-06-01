"""create evs table

Revision ID: 20260601_000001
Revises:
Create Date: 2026-06-01 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260601_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ev_status_enum = postgresql.ENUM(
    "AVAILABLE",
    "LEASED",
    "MAINTENANCE",
    name="ev_status",
    create_type=False,
)


def upgrade() -> None:
    ev_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "evs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("battery_capacity_kwh", sa.Integer(), nullable=False),
        sa.Column("range_miles", sa.Integer(), nullable=False),
        sa.Column("monthly_lease_price", sa.Float(), nullable=False),
        sa.Column("status", ev_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("evs")
    ev_status_enum.drop(op.get_bind(), checkfirst=True)
