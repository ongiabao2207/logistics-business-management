"""create contract service tables

Revision ID: 202608230001
Revises:
Create Date: 2026-08-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "202608230001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contract",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("payment_terms", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contract_customer_id", "contract", ["customer_id"])

    op.create_table(
        "contract_service",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contract_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("service_unit", sa.String(length=100), nullable=False),
        sa.Column("service_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contract.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contract_service_contract_id", "contract_service", ["contract_id"]
    )

    op.create_table(
        "contract_appendix",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contract_id", sa.String(length=36), nullable=False),
        sa.Column("appendix_name", sa.String(length=255), nullable=False),
        sa.Column("change_type", sa.String(length=100), nullable=False),
        sa.Column("new_valid_from", sa.Date(), nullable=True),
        sa.Column("new_valid_to", sa.Date(), nullable=True),
        sa.Column("new_payment_terms", sa.String(length=255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contract.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contract_appendix_contract_id", "contract_appendix", ["contract_id"]
    )

    op.create_table(
        "appendix_change_detail",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("appendix_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("old_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("new_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["appendix_id"], ["contract_appendix.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appendix_change_detail_appendix_id",
        "appendix_change_detail",
        ["appendix_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_appendix_change_detail_appendix_id",
        table_name="appendix_change_detail",
    )
    op.drop_table("appendix_change_detail")
    op.drop_index("ix_contract_appendix_contract_id", table_name="contract_appendix")
    op.drop_table("contract_appendix")
    op.drop_index("ix_contract_service_contract_id", table_name="contract_service")
    op.drop_table("contract_service")
    op.drop_index("ix_contract_customer_id", table_name="contract")
    op.drop_table("contract")
