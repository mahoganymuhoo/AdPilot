"""AI learning loop — impact score columns

Revision ID: 003
Revises: 002
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Strategy tablosuna AI güven skoru
    op.add_column("strategies", sa.Column("ai_confidence_score", sa.Float(), nullable=True))

    # StrategyOutcome tablosuna etki ölçüm kolonları
    op.add_column("strategy_outcomes", sa.Column("impact_score", sa.Float(), nullable=True))
    op.add_column("strategy_outcomes", sa.Column("actual_roas_change_pct", sa.Float(), nullable=True))
    op.add_column("strategy_outcomes", sa.Column("predicted_roas_change_pct", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("strategies", "ai_confidence_score")
    op.drop_column("strategy_outcomes", "impact_score")
    op.drop_column("strategy_outcomes", "actual_roas_change_pct")
    op.drop_column("strategy_outcomes", "predicted_roas_change_pct")
