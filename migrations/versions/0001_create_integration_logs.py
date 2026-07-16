"""create integration_logs

Revision ID: 0001
Revises:
Create Date: 2026-07-14 00:00:00.000000+00:00
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integration_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("integration_name", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column(
            "request_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "response_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_integration_logs_integration_name"),
        "integration_logs",
        ["integration_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_logs_status_code"),
        "integration_logs",
        ["status_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_logs_request_id"),
        "integration_logs",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_logs_timestamp"),
        "integration_logs",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_integration_logs_timestamp"), table_name="integration_logs")
    op.drop_index(op.f("ix_integration_logs_request_id"), table_name="integration_logs")
    op.drop_index(
        op.f("ix_integration_logs_status_code"), table_name="integration_logs"
    )
    op.drop_index(
        op.f("ix_integration_logs_integration_name"), table_name="integration_logs"
    )
    op.drop_table("integration_logs")
