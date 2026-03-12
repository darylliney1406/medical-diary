"""Add audience column to ai_summaries

Revision ID: 003
Revises: 002
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("patient", "professional", name="summaryaudience").create(op.get_bind())
    op.add_column(
        "ai_summaries",
        sa.Column("audience", sa.Enum("patient", "professional", name="summaryaudience"), nullable=False, server_default="professional"),
    )


def downgrade() -> None:
    op.drop_column("ai_summaries", "audience")
    sa.Enum("patient", "professional", name="summaryaudience").drop(op.get_bind())
