"""initial schema with timescaledb hypertable

Revision ID: 001
Revises:
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Platforms
    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("fee_structure", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    # Sellers
    op.create_table(
        "sellers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("shop_name", sa.String(), nullable=True),
        sa.Column("ai_provider", sa.String(), default="claude", nullable=False),
        sa.Column("anthropic_api_key_enc", sa.Text(), nullable=True),
        sa.Column("openai_api_key_enc", sa.Text(), nullable=True),
        sa.Column("default_cogs_percent", sa.Float(), default=0.40),
        sa.Column("target_roas", sa.Float(), default=3.0),
        sa.Column("target_acos", sa.Float(), default=0.30),
        sa.Column("daily_budget", sa.Float(), default=10.0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Platform Connections
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("platform_id", sa.Integer(), sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("data_mode", sa.String(), default="api", nullable=False),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shop_id", sa.String(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("platform_id", sa.Integer(), sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("listing_id", sa.String(), nullable=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("cogs", sa.Float(), nullable=True),
        sa.Column("shipping_cost", sa.Float(), default=0.0),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("inventory", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Ad Metrics (TimescaleDB hypertable)
    op.create_table(
        "ad_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("platform_id", sa.Integer(), sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("impressions", sa.Integer(), default=0),
        sa.Column("clicks", sa.Integer(), default=0),
        sa.Column("ad_spend", sa.Float(), default=0.0),
        sa.Column("revenue", sa.Float(), default=0.0),
        sa.Column("conversions", sa.Integer(), default=0),
        sa.Column("views", sa.Integer(), default=0),
        sa.Column("roas", sa.Float(), nullable=True),
        sa.Column("acos", sa.Float(), nullable=True),
        sa.Column("ctr", sa.Float(), nullable=True),
        sa.Column("conversion_rate", sa.Float(), nullable=True),
        sa.Column("cpc", sa.Float(), nullable=True),
        sa.Column("net_profit", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(), default="api", nullable=False),
    )

    # TimescaleDB hypertable dönüşümü
    op.execute(
        "SELECT create_hypertable('ad_metrics', 'time', if_not_exists => TRUE);"
    )

    # Anomaly Logs
    op.create_table(
        "anomaly_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("z_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Integer(), default=0),
    )

    # AI Insights
    op.create_table(
        "ai_insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("insight_type", sa.String(), nullable=False),
        sa.Column("ai_provider", sa.String(), nullable=False),
        sa.Column("model_used", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), default=0),
        sa.Column("completion_tokens", sa.Integer(), default=0),
        sa.Column("cache_hit", sa.Integer(), default=0),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed: varsayılan platformlar
    op.execute("""
        INSERT INTO platforms (name, display_name, fee_structure) VALUES
        ('etsy', 'Etsy', '{"transaction_fee_pct": 0.065, "listing_fee": 0.20, "offsite_ads_pct": 0.15}'),
        ('amazon', 'Amazon', '{"referral_fee_pct": 0.15, "fba_fee": 3.50}'),
        ('shopify', 'Shopify', '{"transaction_fee_pct": 0.02}'),
        ('tiktok_shop', 'TikTok Shop', '{"commission_pct": 0.08}')
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("ai_insights")
    op.drop_table("anomaly_logs")
    op.drop_table("ad_metrics")
    op.drop_table("products")
    op.drop_table("platform_connections")
    op.drop_table("sellers")
    op.drop_table("platforms")
