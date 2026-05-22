import json
import anthropic
from app.services.llm.base import LLMProvider, AnalysisResult
from app.core.config import settings

SYSTEM_PROMPT = """Sen AdPilot'un kıdemli e-ticaret reklam analistisin.
Etsy başta olmak üzere e-ticaret platformlarında satıcılara reklam karlılığı,
bütçe optimizasyonu ve ürün stratejisi konularında veri odaklı, somut öneriler verirsin.

Temel bilgiler:
- ROAS = Reklam Geliri / Reklam Harcaması (>3.0 iyi, <1.5 zararlı)
- ACOS = Reklam Harcaması / Reklam Geliri × 100 (düşük=iyi)
- TACoS = Toplam Reklam Harcaması / Toplam Gelir × 100
- Break-even ACOS = Kâr Marjı % (bu değerin altında reklam karlı)
- Etsy ücretleri: %6.5 işlem + $0.20 listeleme

Her analizde mutlaka:
1. Net karlılık durumu
2. Break-even ACOS karşılaştırması
3. Somut aksiyon önerisi (bütçe artır/azalt/durdur, ne kadar)
4. Varsa kırmızı bayraklar

Yanıtlarını her zaman geçerli JSON formatında ver."""


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str | None = None):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.ANTHROPIC_API_KEY
        )
        self.model = settings.CLAUDE_MODEL

    async def analyze_profitability(self, metrics: dict, seller_context: dict) -> AnalysisResult:
        prompt = f"""<seller_context>
{json.dumps(seller_context, ensure_ascii=False, indent=2)}
</seller_context>

<metrics>
{json.dumps(metrics, ensure_ascii=False, indent=2)}
</metrics>

<task>
Karlılık analizi yap. Şu formatta JSON döndür:
{{
  "is_profitable": true/false,
  "roas_status": "excellent|good|marginal|poor",
  "acos_vs_breakeven": "below_breakeven (karlı)|above_breakeven (zararlı)",
  "net_profit_per_sale": 0.0,
  "tacos": 0.0,
  "recommendation": "increase_budget|maintain|reduce_budget|pause_ads",
  "budget_change_pct": 0,
  "reasoning": "açıklama",
  "red_flags": ["varsa uyarılar"],
  "action_items": ["somut adımlar"]
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # Prompt cache
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        cache_hit = getattr(usage, "cache_read_input_tokens", 0) > 0

        return AnalysisResult(
            provider="claude",
            model=self.model,
            insight_type="profitability",
            result_json=result_json,
            summary_text=result_json.get("reasoning", ""),
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_hit=cache_hit,
        )

    async def score_ad_worthiness(self, product_metrics: dict, seller_context: dict) -> AnalysisResult:
        prompt = f"""<seller_context>
{json.dumps(seller_context, ensure_ascii=False, indent=2)}
</seller_context>

<product_metrics>
{json.dumps(product_metrics, ensure_ascii=False, indent=2)}
</product_metrics>

<task>
Bu ürün için reklam uygunluk değerlendirmesi yap. Şu formatta JSON döndür:
{{
  "score": 0-100,
  "recommendation": "dont_advertise|test_small_budget|recommend|priority",
  "view_analysis": {{
    "situation": "high_views_low_sales|low_views_good_conversion|low_views_low_conversion|balanced",
    "diagnosis": "açıklama",
    "pre_ad_action": "varsa reklam öncesi yapılması gereken (listing düzeltme vb.) veya null"
  }},
  "profit_margin_ok": true/false,
  "inventory_ok": true/false,
  "trend_ok": true/false,
  "seasonal_score": 0.0-1.0,
  "reasoning": "gerekçe",
  "suggested_daily_budget": 0.0
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude",
            model=self.model,
            insight_type="ad_worthiness",
            result_json=result_json,
            summary_text=result_json.get("reasoning", ""),
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )

    async def detect_anomaly_cause(self, anomaly: dict, history: list[dict]) -> AnalysisResult:
        prompt = f"""<anomaly>
{json.dumps(anomaly, ensure_ascii=False, indent=2)}
</anomaly>

<history_last_7_days>
{json.dumps(history, ensure_ascii=False, indent=2)}
</history_last_7_days>

<task>
Bu anomalinin olası nedenlerini ve alınması gereken önlemleri analiz et. JSON formatında döndür:
{{
  "likely_causes": ["neden1", "neden2"],
  "urgency": "low|medium|high|critical",
  "recommended_actions": ["adım1", "adım2"],
  "monitor_metrics": ["takip edilecek metrikler"],
  "reasoning": "açıklama"
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude",
            model=self.model,
            insight_type="anomaly",
            result_json=result_json,
            summary_text=result_json.get("reasoning", ""),
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )

    async def generate_budget_recommendation(self, products: list[dict], total_budget: float) -> AnalysisResult:
        prompt = f"""<total_daily_budget>{total_budget}</total_daily_budget>

<products>
{json.dumps(products, ensure_ascii=False, indent=2)}
</products>

<task>
Bu ürün portföyü için günlük {total_budget}$ bütçeyi en verimli şekilde dağıt. JSON formatında döndür:
{{
  "allocations": [
    {{"product_id": 1, "product_title": "...", "suggested_budget": 0.0, "reason": "..."}}
  ],
  "total_allocated": 0.0,
  "strategy_summary": "genel strateji açıklaması",
  "paused_products": ["reklam durdurulması önerilen ürünler"]
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude",
            model=self.model,
            insight_type="recommendation",
            result_json=result_json,
            summary_text=result_json.get("strategy_summary", ""),
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )

    async def launch_strategy(
        self,
        recommendation: dict,
        initial_metrics: dict,
        seller_context: dict,
        action_confirmed: str,
    ) -> AnalysisResult:
        prompt = f"""<seller_context>
{json.dumps(seller_context, ensure_ascii=False, indent=2)}
</seller_context>

<original_recommendation>
{json.dumps(recommendation, ensure_ascii=False, indent=2)}
</original_recommendation>

<initial_metrics>
{json.dumps(initial_metrics, ensure_ascii=False, indent=2)}
</initial_metrics>

<action_confirmed_by_seller>
{action_confirmed}
</action_confirmed_by_seller>

<task>
Satıcı bu aksiyonu aldı. Bu kararı değerlendir, başarı hedeflerini say ve takip takvimi oluştur.
JSON formatında döndür:
{{
  "strategy_name": "kısa açıklayıcı isim (ör: Seramik Kupa — Bütçe Artışı)",
  "operation_type": "increase_budget|reduce_budget|pause_ads|optimize_listing|test_budget",
  "goal_summary": "tek cümle hedef",
  "target_metrics": {{
    "roas": 0.0,
    "acos": 0.0,
    "daily_revenue": 0.0,
    "conversions_per_day": 0.0
  }},
  "timeline_days": 14,
  "check_interval_days": 3,
  "success_criteria": ["kriter 1", "kriter 2", "kriter 3"],
  "watch_metrics": ["ROAS", "CTR", "ACOS"],
  "risk_factors": ["risk 1", "risk 2"],
  "baseline_summary": "başlangıç durumu kısa özeti",
  "action_assessment": "alınan aksiyonun değerlendirmesi",
  "confidence": "low|medium|high",
  "reasoning": "genel gerekçe"
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude", model=self.model, insight_type="strategy_launch",
            result_json=result_json, summary_text=result_json.get("goal_summary", ""),
            prompt_tokens=usage.input_tokens, completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )

    async def monitor_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        current_metrics: dict,
        days_elapsed: int,
        days_remaining: int,
    ) -> AnalysisResult:
        prompt = f"""<strategy>
{json.dumps(strategy, ensure_ascii=False, indent=2)}
</strategy>

<checkpoint_history>
{json.dumps(checkpoints, ensure_ascii=False, indent=2)}
</checkpoint_history>

<current_metrics>
{json.dumps(current_metrics, ensure_ascii=False, indent=2)}
</current_metrics>

<timeline>
Başlangıçtan bu yana geçen gün: {days_elapsed}
Kalan gün: {days_remaining}
</timeline>

<task>
Bu stratejinin gidişatını değerlendir. Hedeflere ulaşılıyor mu?
Geçmiş checkpoint'leri ile bugünkü durumu karşılaştır, trend çiz.
JSON formatında döndür:
{{
  "status": "on_track|at_risk|off_track",
  "progress_pct": 0.0,
  "metric_deltas": {{
    "roas_change": 0.0,
    "acos_change": 0.0,
    "revenue_change_pct": 0.0
  }},
  "trend": "improving|stable|declining",
  "milestone_hit": true/false,
  "adjustment_needed": true/false,
  "adjustment": {{
    "type": "increase_budget|decrease_budget|pause|none",
    "amount_pct": 0,
    "reason": "neden"
  }},
  "checkpoint_insight": "bu kontrol noktasında ne görüyoruz",
  "red_flags": [],
  "next_checkpoint_focus": "bir sonraki kontrolde neye bakacağız",
  "reasoning": "detaylı değerlendirme"
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude", model=self.model, insight_type="strategy_monitor",
            result_json=result_json, summary_text=result_json.get("checkpoint_insight", ""),
            prompt_tokens=usage.input_tokens, completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )

    async def verdict_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        final_metrics: dict,
    ) -> AnalysisResult:
        prompt = f"""<strategy>
{json.dumps(strategy, ensure_ascii=False, indent=2)}
</strategy>

<checkpoint_history>
{json.dumps(checkpoints, ensure_ascii=False, indent=2)}
</checkpoint_history>

<final_metrics>
{json.dumps(final_metrics, ensure_ascii=False, indent=2)}
</final_metrics>

<task>
Strateji süresi doldu. Tüm süreci değerlendir. Başlangıçtan bugüne ne değişti?
Hedeflere ulaşıldı mı? Öğrenilenleri çıkar. Bir sonraki stratejiye ne taşımalıyız?
JSON formatında döndür:
{{
  "outcome": "success|partial|failed",
  "outcome_summary": "tek cümle sonuç",
  "metric_results": {{
    "roas_start": 0.0, "roas_end": 0.0, "roas_target": 0.0, "roas_achieved": true/false,
    "acos_start": 0.0, "acos_end": 0.0, "acos_target": 0.0, "acos_achieved": true/false,
    "revenue_change_pct": 0.0
  }},
  "success_criteria_results": [
    {{"criterion": "...", "met": true/false, "detail": "..."}}
  ],
  "what_worked": ["iyi giden 1", "iyi giden 2"],
  "what_failed": ["kötü giden 1"],
  "lessons_learned": ["öğrenilen 1", "öğrenilen 2"],
  "next_strategy_hints": {{
    "recommended_action": "ne yapmalı",
    "suggested_budget": 0.0,
    "focus_area": "bütçe|listing|timing|targeting",
    "context_for_next_ai": "bir sonraki AI çağrısına taşınacak kritik bağlam"
  }},
  "verdict_reasoning": "kapsamlı değerlendirme"
}}
</task>"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1800,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            result_json = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result_json = json.loads(match.group()) if match else {"raw": text}

        usage = response.usage
        return AnalysisResult(
            provider="claude", model=self.model, insight_type="strategy_verdict",
            result_json=result_json, summary_text=result_json.get("outcome_summary", ""),
            prompt_tokens=usage.input_tokens, completion_tokens=usage.output_tokens,
            cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
        )
