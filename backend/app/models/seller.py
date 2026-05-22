from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    shop_name = Column(String, nullable=True)

    # AI Provider seçimi: "claude" veya "openai"
    ai_provider = Column(String, default="claude", nullable=False)
    anthropic_api_key_enc = Column(Text, nullable=True)
    openai_api_key_enc = Column(Text, nullable=True)

    # Varsayılan değerler
    default_cogs_percent = Column(Float, default=0.40)  # Gelirin %40'ı maliyet
    target_roas = Column(Float, default=3.0)
    target_acos = Column(Float, default=0.30)
    daily_budget = Column(Float, default=10.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    products = relationship("Product", back_populates="seller", lazy="dynamic")
    platform_connections = relationship("PlatformConnection", back_populates="seller", lazy="dynamic")
