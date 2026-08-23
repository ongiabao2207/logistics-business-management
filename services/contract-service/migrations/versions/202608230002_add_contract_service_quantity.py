"""add contract service quantity

Revision ID: 202608230002
Revises: 202608230001
Create Date: 2026-08-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "202608230002"
down_revision: str | None = "202608230001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contract_service",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("contract_service", "quantity", server_default=None)


def downgrade() -> None:
    op.drop_column("contract_service", "quantity")
