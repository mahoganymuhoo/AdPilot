import json
from openai import AsyncOpenAI
from app.services.llm.base import LLMProvider, AnalysisResult
from app.core.config import settings

SYSTEM_PROMPT = """You are AdPilot's senior e-commerce advertising analyst.
You provide data-driven, actionable recommendations on ad profitability,
budget optimization, and product strategy for sellers on Etsy and other platforms.

Key metrics:
- ROAS = Ad Revenue / Ad Spend (>3.0 good, <1.5 harmful)
- ACOS = Ad Spend / Ad Revenue × 100 (lower is better)
- TACoS = Total Ad Spend / Total Revenue × 100
- Break-even ACOS = Profit Margin % (ads profitable below this value)
- Etsy fees: 6.5% transaction + $0.20 listing

Always include in analysis:
1. Net profitability status
2. Break-even ACOS comparison
3. Concrete action recommendation with amounts
4. Red flags if any

Always respond in valid JSON format."""


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def _call(self, user_content: str, max_tokens: int = 1024) -> tuple[dict, int, int]:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or "{}"
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            result_json = {"raw": text}
        usage = response.usage
        return result_json, usage.prompt_tokens, usage.completion_tokens

    async def analyze_profitability(self, metrics: dict, seller_context: dict) -> AnalysisResult:
        prompt = f"""Seller context: {json.dumps(seller_context)}
Metrics: {json.dumps(metrics)}

Analyze profitability and return JSON:
{{
  "is_profitable": true/false,
  "roas_status": "excellent|good|marginal|poor",
  "acos_vs_breakeven": "below_breakeven|above_breakeven",
  "net_profit_per_sale": 0.0,
  "tacos": 0.0,
  "recommendation": "increase_budget|maintain|reduce_budget|pause_ads",
  "budget_change_pct": 0,
  "reasoning": "explanation",
  "red_flags": [],
  "action_items": []
}}"""
        result_json, pt, ct = await self._call(prompt)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="profitability",
            result_json=result_json, summary_text=result_json.get("reasoning", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )

    async def score_ad_worthiness(self, product_metrics: dict, seller_context: dict) -> AnalysisResult:
        prompt = f"""Seller context: {json.dumps(seller_context)}
Product metrics: {json.dumps(product_metrics)}

Score ad worthiness and return JSON:
{{
  "score": 0-100,
  "recommendation": "dont_advertise|test_small_budget|recommend|priority",
  "view_analysis": {{
    "situation": "high_views_low_sales|low_views_good_conversion|low_views_low_conversion|balanced",
    "diagnosis": "...",
    "pre_ad_action": null
  }},
  "profit_margin_ok": true/false,
  "inventory_ok": true/false,
  "trend_ok": true/false,
  "seasonal_score": 0.0,
  "reasoning": "...",
  "suggested_daily_budget": 0.0
}}"""
        result_json, pt, ct = await self._call(prompt)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="ad_worthiness",
            result_json=result_json, summary_text=result_json.get("reasoning", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )

    async def detect_anomaly_cause(self, anomaly: dict, history: list[dict]) -> AnalysisResult:
        prompt = f"""Anomaly: {json.dumps(anomaly)}
History (last 7 days): {json.dumps(history)}

Analyze anomaly and return JSON:
{{
  "likely_causes": [],
  "urgency": "low|medium|high|critical",
  "recommended_actions": [],
  "monitor_metrics": [],
  "reasoning": "..."
}}"""
        result_json, pt, ct = await self._call(prompt, max_tokens=800)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="anomaly",
            result_json=result_json, summary_text=result_json.get("reasoning", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )

    async def generate_budget_recommendation(self, products: list[dict], total_budget: float) -> AnalysisResult:
        prompt = f"""Total daily budget: ${total_budget}
Products: {json.dumps(products)}

Allocate budget optimally and return JSON:
{{
  "allocations": [{{"product_id": 1, "product_title": "...", "suggested_budget": 0.0, "reason": "..."}}],
  "total_allocated": 0.0,
  "strategy_summary": "...",
  "paused_products": []
}}"""
        result_json, pt, ct = await self._call(prompt, max_tokens=1500)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="recommendation",
            result_json=result_json, summary_text=result_json.get("strategy_summary", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )
