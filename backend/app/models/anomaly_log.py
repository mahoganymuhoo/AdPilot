from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    metric_name = Column(String, nullable=False)   # "roas", "acos", "ctr", "conversion_rate"
    metric_value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    severity = Column(String, nullable=False)       # "warning" | "critical"
    direction = Column(String, nullable=False)      # "spike" | "drop"
    message = Column(Text, nullable=False)
    is_resolved = Column(Integer, default=0)       # 0=açık, 1=kapatıldı

    product = relationship("Product")
