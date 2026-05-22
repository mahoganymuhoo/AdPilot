"""
Prompt Cache Yöneticisi

Claude'un `cache_control: ephemeral` özelliğini maksimize eder.
Seller başına önceden hesaplanmış bağlamı cache'e yazarak
tekrarlayan sorgularda ~%90 token tasarrufu sağlar.

Cache TTL: Ephemeral cache Anthropic tarafında ~5 dakika tutulur.
Bu modül büyük seller context'ini bir kez oluşturup her çağrıda
yeniden kullanır — küçük, değişken kısım (soru) cache'e girmez.

Token maliyet takibi: Her AI çağrısından gelen kullanım verisini
toplar. Settings sayfasındaki maliyet dashboard'u için veri kaynağı.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# Antropik fiyatlandırması (claude-sonnet-4-6, 2026 Q2 itibariyle)
# Gerçek fiyatlar için https://www.anthropic.com/pricing adresini kontrol et
PRICE_PER_1K = {
    "input": 0.003,          # $0.003 / 1K input token
    "output": 0.015,         # $0.015 / 1K output token
    "cache_write": 0.00375,  # $0.00375 / 1K cache write token
    "cache_read": 0.0003,    # $0.0003 / 1K cache read token (10x ucuz)
}


@dataclass
class UsageRecord:
    """Tek bir AI çağrısının token kullanımı."""
    timestamp: datetime
    seller_id: int
    insight_type: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        return (
            self.input_tokens * PRICE_PER_1K["input"] / 1000
            + self.output_tokens * PRICE_PER_1K["output"] / 1000
            + self.cache_write_tokens * PRICE_PER_1K["cache_write"] / 1000
            + self.cache_read_tokens * PRICE_PER_1K["cache_read"] / 1000
        )

    @property
    def saved_cost_usd(self) -> float:
        """Cache hit olmadan ne kadar öderdiniz?"""
        would_have_paid = self.cache_read_tokens * PRICE_PER_1K["input"] / 1000
        actually_paid = self.cache_read_tokens * PRICE_PER_1K["cache_read"] / 1000
        return round(would_have_paid - actually_paid, 6)


@dataclass
class TokenBudgetSummary:
    """Bir dönem için toplam token ve maliyet özeti."""
    period: str             # "today" | "this_week" | "this_month"
    total_input: int
    total_output: int
    total_cache_read: int
    total_cache_write: int
    total_cost_usd: float
    saved_cost_usd: float
    cache_hit_rate_pct: float
    call_count: int
    by_type: dict[str, dict] = field(default_factory=dict)


class PromptCacheManager:
    """
    Seller başına cache'lenmiş bağlam oluşturur ve yönetir.
    Usage kayıtlarını bellekte tutar (production'da Redis/DB'ye taşı).
    """

    def __init__(self):
        self._seller_contexts: dict[int, dict] = {}
        self._usage_records: list[UsageRecord] = []

    def build_seller_context(
        self,
        seller: Any,  # Seller model instance
        products: list[dict],
        recent_strategies: list[dict] | None = None,
    ) -> dict:
        """
        Seller'ın tüm statik bağlamını tek seferde oluşturur.
        Bu bağlam cache_control: ephemeral ile gönderilir → ~5 dakika cache'de kalır.

        Yapı:
        - Seller hedefleri ve platform bilgisi
        - Ürün portföyü (tüm aktif ürünler)
        - Geçmiş strateji performansı (varsa)
        """
        context = {
            "seller": {
                "target_roas": seller.target_roas,
                "target_acos": seller.target_acos,
                "daily_budget": seller.daily_budget,
                "default_cogs_percent": seller.default_cogs_percent,
                "ai_provider": seller.ai_provider,
            },
            "portfolio": {
                "product_count": len(products),
                "products": [
                    {
                        "id": p.get("id"),
                        "title": p.get("title", "")[:60],
                        "price": p.get("price"),
                        "cogs": p.get("cogs"),
                        "category": p.get("category"),
                    }
                    for p in products[:20]  # İlk 20 ürün (context boyutu kontrolü)
                ],
            },
        }

        if recent_strategies:
            success_count = sum(1 for s in recent_strategies if s.get("outcome") == "success")
            context["strategy_history"] = {
                "total": len(recent_strategies),
                "success_rate_pct": round(success_count / len(recent_strategies) * 100, 1) if recent_strategies else 0,
                "recent_3": recent_strategies[:3],
            }

        self._seller_contexts[seller.id] = context
        return context

    def get_cached_context(self, seller_id: int) -> dict | None:
        """Önbelleğe alınmış seller bağlamını döndür."""
        return self._seller_contexts.get(seller_id)

    def record_usage(
        self,
        seller_id: int,
        insight_type: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> UsageRecord:
        """Bir AI çağrısının kullanımını kaydet."""
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc),
            seller_id=seller_id,
            insight_type=insight_type,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        )
        self._usage_records.append(record)
        return record

    def get_cost_summary(
        self,
        seller_id: int,
        period_days: int = 30,
    ) -> TokenBudgetSummary:
        """Belirtilen dönem için token ve maliyet özeti."""
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(days=period_days)
        records = [
            r for r in self._usage_records
            if r.seller_id == seller_id and r.timestamp >= since
        ]

        if not records:
            return TokenBudgetSummary(
                period=f"son {period_days} gün",
                total_input=0, total_output=0,
                total_cache_read=0, total_cache_write=0,
                total_cost_usd=0.0, saved_cost_usd=0.0,
                cache_hit_rate_pct=0.0, call_count=0,
            )

        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cache_read = sum(r.cache_read_tokens for r in records)
        total_cache_write = sum(r.cache_write_tokens for r in records)
        total_cost = sum(r.cost_usd for r in records)
        saved = sum(r.saved_cost_usd for r in records)

        cache_hits = sum(1 for r in records if r.cache_read_tokens > 0)
        cache_hit_rate = (cache_hits / len(records)) * 100 if records else 0

        # Tip bazında breakdown
        by_type: dict[str, dict] = {}
        for r in records:
            t = r.insight_type
            if t not in by_type:
                by_type[t] = {"count": 0, "cost_usd": 0.0, "input_tokens": 0}
            by_type[t]["count"] += 1
            by_type[t]["cost_usd"] = round(by_type[t]["cost_usd"] + r.cost_usd, 6)
            by_type[t]["input_tokens"] += r.input_tokens

        return TokenBudgetSummary(
            period=f"son {period_days} gün",
            total_input=total_input,
            total_output=total_output,
            total_cache_read=total_cache_read,
            total_cache_write=total_cache_write,
            total_cost_usd=round(total_cost, 4),
            saved_cost_usd=round(saved, 4),
            cache_hit_rate_pct=round(cache_hit_rate, 1),
            call_count=len(records),
            by_type=by_type,
        )


# Singleton — uygulama genelinde tek instance
cache_manager = PromptCacheManager()
