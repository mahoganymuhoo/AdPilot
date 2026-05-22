from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class ManualMetricEntry(BaseModel):
    """Manuel form girişi için."""
    date: str                         # "2024-01-15"
    listing_id: str
    title: str | None = None
    impressions: int = 0
    clicks: int = 0
    ad_spend: float = 0.0
    revenue: float = 0.0
    conversions: int = 0
    views: int = 0


class MetricsRead(BaseModel):
    id: int
    time: datetime
    product_id: int
    impressions: int
    clicks: int
    ad_spend: float
    revenue: float
    conversions: int
    views: int
    roas: float | None
    acos: float | None
    ctr: float | None
    conversion_rate: float | None
    net_profit: float | None
    data_source: str

    model_config = {"from_attributes": True}


class ProfitabilityResponse(BaseModel):
    product_id: int
    product_title: str
    roas: float
    acos: float
    tacos: float
    break_even_acos: float
    net_profit_per_sale: float
    is_profitable: bool
    profit_margin: float
    recommendation: Literal["increase_budget", "maintain", "reduce_budget", "pause_ads"]
    budget_change_pct: int
    ema_7d: float
    ema_30d: float
    trend: Literal["improving", "stable", "declining"]
    anomalies: list[dict]
