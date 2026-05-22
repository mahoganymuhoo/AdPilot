from pydantic import BaseModel
from typing import Any


class InsightResponse(BaseModel):
    id: int | None = None
    product_id: int | None
    insight_type: str
    ai_provider: str
    model_used: str
    result_json: dict[str, Any]
    summary_text: str
    prompt_tokens: int
    completion_tokens: int
    cache_hit: bool


class AdWorthinessResponse(BaseModel):
    product_id: int
    product_title: str
    score: int
    recommendation: str
    view_situation: str
    view_diagnosis: str
    pre_ad_action: str | None
    reasons: list[str]
    suggested_daily_budget: float
    ai_analysis: dict[str, Any] | None = None


class BudgetRecommendationResponse(BaseModel):
    total_budget: float
    allocations: list[dict[str, Any]]
    paused_products: list[str]
    strategy_summary: str
    ai_analysis: dict[str, Any] | None = None
