from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    name = Column(String(200), nullable=False)
    operation_type = Column(String(50), nullable=False)
    status = Column(String(20), default="active", nullable=False)

    initiated_at = Column(DateTime, default=datetime.utcnow)
    target_date = Column(DateTime, nullable=False)

    initial_metrics = Column(JSON, nullable=False)
    target_metrics = Column(JSON, nullable=False)
    ai_launch_analysis = Column(JSON)

    # AI'ın başlangıçtaki güven skoru (low/medium/high → 0.33/0.66/1.0)
    ai_confidence_score = Column(Float, nullable=True)

    check_interval_days = Column(Integer, default=3)

    checkpoints = relationship(
        "StrategyCheckpoint",
        back_populates="strategy",
        order_by="StrategyCheckpoint.checked_at",
    )
    outcome = relationship("StrategyOutcome", back_populates="strategy", uselist=False)


class StrategyCheckpoint(Base):
    __tablename__ = "strategy_checkpoints"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)

    checked_at = Column(DateTime, default=datetime.utcnow)
    current_metrics = Column(JSON, nullable=False)
    ai_analysis = Column(JSON, nullable=False)
    seller_note = Column(String(500), nullable=True)

    progress_pct = Column(Float)
    status = Column(String(20))  # on_track | at_risk | off_track

    strategy = relationship("Strategy", back_populates="checkpoints")


class StrategyOutcome(Base):
    __tablename__ = "strategy_outcomes"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), unique=True, nullable=False)

    completed_at = Column(DateTime, default=datetime.utcnow)
    outcome = Column(String(20), nullable=False)  # success | partial | failed

    final_metrics = Column(JSON, nullable=False)
    ai_verdict = Column(JSON, nullable=False)

    lessons_learned = Column(JSON)
    next_strategy_hints = Column(JSON)

    # Etki skoru: AI güven skoru × gerçek sonuç kalitesi (0-1)
    # Hesaplama: impact_score = outcome_quality × confidence_match
    impact_score = Column(Float, nullable=True)
    # Gerçek ROAS değişimi (başlangıç→sonuç)
    actual_roas_change_pct = Column(Float, nullable=True)
    # AI'ın tahmin ettiği değişim
    predicted_roas_change_pct = Column(Float, nullable=True)

    strategy = relationship("Strategy", back_populates="outcome")
