"""create energy tariffs table

Revision ID: d16281dd4b0b
Revises: 20260601_000001
Create Date: 2026-06-04 16:41:33.231272
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d16281dd4b0b"
down_revision: Union[str, None] = "20260601_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "energy_tariffs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price_per_kwh", sa.Float(), nullable=False),
        sa.Column("ev_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["ev_id"], ["evs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_energy_tariffs_ev_id"), "energy_tariffs", ["ev_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_energy_tariffs_ev_id"), table_name="energy_tariffs")
    op.drop_table("energy_tariffs")
