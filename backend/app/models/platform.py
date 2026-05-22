from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # "etsy", "amazon", "shopify"
    display_name = Column(String, nullable=False)
    # Ücret yapısı JSON: {"transaction_fee_pct": 0.065, "listing_fee": 0.20, ...}
    fee_structure = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)

    connections = relationship("PlatformConnection", back_populates="platform")


class PlatformConnection(Base):
    """Her seller'ın her platforma bağlantı bilgileri."""
    __tablename__ = "platform_connections"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    # Veri giriş modu: "api" | "csv" | "manual"
    data_mode = Column(String, default="api", nullable=False)

    # OAuth token bilgileri (şifreli)
    access_token_enc = Column(Text, nullable=True)
    refresh_token_enc = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    shop_id = Column(String, nullable=True)

    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    seller = relationship("Seller", back_populates="platform_connections")
    platform = relationship("Platform", back_populates="connections")
