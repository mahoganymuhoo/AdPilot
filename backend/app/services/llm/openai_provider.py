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

    async def launch_strategy(
        self,
        recommendation: dict,
        initial_metrics: dict,
        seller_context: dict,
        action_confirmed: str,
    ) -> AnalysisResult:
        prompt = f"""Seller context: {json.dumps(seller_context)}
Original recommendation: {json.dumps(recommendation)}
Initial metrics: {json.dumps(initial_metrics)}
Action confirmed by seller: {action_confirmed}

Evaluate this action and set success targets with a monitoring schedule. Return JSON:
{{
  "strategy_name": "short descriptive name",
  "operation_type": "increase_budget|reduce_budget|pause_ads|optimize_listing|test_budget",
  "goal_summary": "one sentence goal",
  "target_metrics": {{"roas": 0.0, "acos": 0.0, "daily_revenue": 0.0, "conversions_per_day": 0.0}},
  "timeline_days": 14,
  "check_interval_days": 3,
  "success_criteria": [],
  "watch_metrics": [],
  "risk_factors": [],
  "baseline_summary": "...",
  "action_assessment": "...",
  "confidence": "low|medium|high",
  "reasoning": "..."
}}"""
        result_json, pt, ct = await self._call(prompt, max_tokens=1200)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="strategy_launch",
            result_json=result_json, summary_text=result_json.get("goal_summary", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )

    async def monitor_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        current_metrics: dict,
        days_elapsed: int,
        days_remaining: int,
    ) -> AnalysisResult:
        prompt = f"""Strategy: {json.dumps(strategy)}
Checkpoint history: {json.dumps(checkpoints)}
Current metrics: {json.dumps(current_metrics)}
Days elapsed: {days_elapsed}, Days remaining: {days_remaining}

Evaluate strategy progress vs targets. Return JSON:
{{
  "status": "on_track|at_risk|off_track",
  "progress_pct": 0.0,
  "metric_deltas": {{"roas_change": 0.0, "acos_change": 0.0, "revenue_change_pct": 0.0}},
  "trend": "improving|stable|declining",
  "milestone_hit": true,
  "adjustment_needed": false,
  "adjustment": {{"type": "none", "amount_pct": 0, "reason": ""}},
  "checkpoint_insight": "...",
  "red_flags": [],
  "next_checkpoint_focus": "...",
  "reasoning": "..."
}}"""
        result_json, pt, ct = await self._call(prompt, max_tokens=1200)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="strategy_monitor",
            result_json=result_json, summary_text=result_json.get("checkpoint_insight", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )

    async def verdict_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        final_metrics: dict,
    ) -> AnalysisResult:
        prompt = f"""Strategy: {json.dumps(strategy)}
All checkpoints: {json.dumps(checkpoints)}
Final metrics: {json.dumps(final_metrics)}

Strategy period is over. Evaluate the full journey, compare to targets, extract lessons.
Return JSON:
{{
  "outcome": "success|partial|failed",
  "outcome_summary": "one sentence result",
  "metric_results": {{
    "roas_start": 0.0, "roas_end": 0.0, "roas_target": 0.0, "roas_achieved": true,
    "acos_start": 0.0, "acos_end": 0.0, "acos_target": 0.0, "acos_achieved": true,
    "revenue_change_pct": 0.0
  }},
  "success_criteria_results": [],
  "what_worked": [],
  "what_failed": [],
  "lessons_learned": [],
  "next_strategy_hints": {{
    "recommended_action": "...",
    "suggested_budget": 0.0,
    "focus_area": "budget|listing|timing|targeting",
    "context_for_next_ai": "critical context to carry forward"
  }},
  "verdict_reasoning": "..."
}}"""
        result_json, pt, ct = await self._call(prompt, max_tokens=1800)
        return AnalysisResult(
            provider="openai", model=self.model, insight_type="strategy_verdict",
            result_json=result_json, summary_text=result_json.get("outcome_summary", ""),
            prompt_tokens=pt, completion_tokens=ct,
        )
