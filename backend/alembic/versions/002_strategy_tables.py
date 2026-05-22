"""strategy tracking tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("initiated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("target_date", sa.DateTime(), nullable=False),
        sa.Column("initial_metrics", JSONB(), nullable=False),
        sa.Column("target_metrics", JSONB(), nullable=False),
        sa.Column("ai_launch_analysis", JSONB(), nullable=True),
        sa.Column("check_interval_days", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_index("ix_strategies_seller_id", "strategies", ["seller_id"])
    op.create_index("ix_strategies_status", "strategies", ["status"])

    op.create_table(
        "strategy_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strategy_id", sa.Integer(), sa.ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checked_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("current_metrics", JSONB(), nullable=False),
        sa.Column("ai_analysis", JSONB(), nullable=False),
        sa.Column("seller_note", sa.Text(), nullable=True),
        sa.Column("progress_pct", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
    )
    op.create_index("ix_strategy_checkpoints_strategy_id", "strategy_checkpoints", ["strategy_id"])

    op.create_table(
        "strategy_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strategy_id", sa.Integer(), sa.ForeignKey("strategies.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("final_metrics", JSONB(), nullable=False),
        sa.Column("ai_verdict", JSONB(), nullable=False),
        sa.Column("lessons_learned", JSONB(), nullable=True),
        sa.Column("next_strategy_hints", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("strategy_outcomes")
    op.drop_table("strategy_checkpoints")
    op.drop_index("ix_strategies_status", "strategies")
    op.drop_index("ix_strategies_seller_id", "strategies")
    op.drop_table("strategies")
