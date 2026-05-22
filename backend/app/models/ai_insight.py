from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AIInsight(Base):
    """Claude veya OpenAI tarafından üretilen analiz ve önerileri saklar."""
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)

    insight_type = Column(String, nullable=False)  # "profitability" | "recommendation" | "anomaly" | "ad_worthiness"
    ai_provider = Column(String, nullable=False)   # "claude" | "openai"
    model_used = Column(String, nullable=False)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cache_hit = Column(Integer, default=0)  # Claude prompt cache kullanıldı mı

    # Yapısal AI çıktısı
    result_json = Column(JSON, nullable=False, default={})
    summary_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="ai_insights")
