from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AdMetric(Base):
    """
    TimescaleDB hypertable olarak kullanılır (alembic migration'da CREATE INDEX ve
    select_hypertable çağrısı yapılır).
    Saatlik granülaritede reklam performans verisi.
    """
    __tablename__ = "ad_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), nullable=False, index=True)  # Partition key
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    # Ham metrikler
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ad_spend = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    views = Column(Integer, default=0)  # Organik görüntülenme

    # Hesaplanan metrikler (denormalize — hızlı sorgu için)
    roas = Column(Float, nullable=True)        # revenue / ad_spend
    acos = Column(Float, nullable=True)        # ad_spend / revenue * 100
    ctr = Column(Float, nullable=True)         # clicks / impressions * 100
    conversion_rate = Column(Float, nullable=True)  # conversions / clicks * 100
    cpc = Column(Float, nullable=True)         # ad_spend / clicks
    net_profit = Column(Float, nullable=True)  # revenue - cogs - fees - ad_spend

    # Kaynak: "api" | "csv" | "manual"
    data_source = Column(String, default="api", nullable=False)

    product = relationship("Product", back_populates="ad_metrics")
