"""Create role and account tables and seed system roles."""

from alembic import op
import sqlalchemy as sa


revision = "202608300001"
down_revision = None
branch_labels = None
depends_on = None


ROLES = (
    ("ROLE_SALE", "Nhân viên Kinh doanh"),
    ("ROLE_OPERATION", "Nhân viên Khai thác"),
    ("ROLE_ACCOUNTANT", "Nhân viên Kế toán"),
    ("ROLE_LEGAL", "Nhân viên Pháp chế"),
    ("ROLE_DIRECTOR", "Ban Giám đốc"),
    ("ROLE_ADMIN", "Quản trị hệ thống"),
)


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_role_name", "role", ["name"])
    op.create_table(
        "account",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_account_email", "account", ["email"])
    op.create_index("ix_account_role_id", "account", ["role_id"])
    op.create_index("ix_account_username", "account", ["username"])
    role_table = sa.table("role", sa.column("name", sa.String), sa.column("description", sa.String))
    op.bulk_insert(role_table, [{"name": name, "description": description} for name, description in ROLES])


def downgrade() -> None:
    op.drop_table("account")
    op.drop_table("role")
