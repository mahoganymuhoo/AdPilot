from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    listing_id = Column(String, nullable=True)  # Platform'dan gelen ID (Etsy listing_id vb.)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    # Seller tarafından girilen maliyet bilgileri
    cogs = Column(Float, nullable=True)        # Cost of Goods Sold (ürün maliyeti)
    shipping_cost = Column(Float, default=0.0)
    price = Column(Float, nullable=True)

    inventory = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    seller = relationship("Seller", back_populates="products")
    ad_metrics = relationship("AdMetric", back_populates="product", lazy="dynamic")
    ai_insights = relationship("AIInsight", back_populates="product", lazy="dynamic")
