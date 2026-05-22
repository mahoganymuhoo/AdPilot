"""
Settings API

- Seller ayarları (AI provider, hedefler)
- Token maliyet dashboard verisi
- Platform bağlantı durumu
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.seller import Seller
from app.models.ai_insight import AIInsight
from app.services.llm.cache_manager import cache_manager

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/token-costs")
async def get_token_costs(
    seller_id: int = 1,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """
    Token kullanımı ve tahmini maliyet özeti.
    Cache hit oranı, tasarruf miktarı ve çağrı tipi dağılımı.
    """
    # In-memory cache manager'dan özet al
    summary = cache_manager.get_cost_summary(seller_id=seller_id, period_days=days)

    # DB'den gerçek AIInsight kayıtlarından da veri çek
    since = datetime.now(timezone.utc)
    from datetime import timedelta
    since -= timedelta(days=days)

    q = await db.execute(
        select(AIInsight)
        .where(AIInsight.seller_id == seller_id, AIInsight.created_at >= since)
        .order_by(AIInsight.created_at.desc())
    )
    insights = q.scalars().all()

    db_input_tokens = sum(i.prompt_tokens or 0 for i in insights)
    db_output_tokens = sum(i.completion_tokens or 0 for i in insights)
    db_cache_hits = sum(1 for i in insights if i.cache_hit)
    db_total_calls = len(insights)

    # DB tokenleri üzerinden maliyet tahmini (cache yokmuş gibi)
    from app.services.llm.cache_manager import PRICE_PER_1K
    db_cost_est = (
        db_input_tokens * PRICE_PER_1K["input"] / 1000
        + db_output_tokens * PRICE_PER_1K["output"] / 1000
    )
    db_saved_est = db_cache_hits * (
        # Ortalama 500 token cache_read → savings
        500 * (PRICE_PER_1K["input"] - PRICE_PER_1K["cache_read"]) / 1000
    )

    by_type: dict[str, int] = {}
    for i in insights:
        t = i.insight_type or "unknown"
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "seller_id": seller_id,
        "period_days": days,
        "total_calls": db_total_calls,
        "cache_hit_count": db_cache_hits,
        "cache_hit_rate_pct": round(db_cache_hits / db_total_calls * 100, 1) if db_total_calls else 0,
        "tokens": {
            "input": db_input_tokens,
            "output": db_output_tokens,
            "total": db_input_tokens + db_output_tokens,
        },
        "cost": {
            "estimated_usd": round(db_cost_est, 4),
            "saved_usd": round(db_saved_est, 4),
            "currency": "USD",
            "note": "Tahmin — gerçek faturanız Anthropic/OpenAI hesabınızda görünür",
        },
        "by_type": by_type,
        "price_reference": {
            "claude_input_per_1k": PRICE_PER_1K["input"],
            "claude_output_per_1k": PRICE_PER_1K["output"],
            "cache_read_per_1k": PRICE_PER_1K["cache_read"],
            "cache_write_per_1k": PRICE_PER_1K["cache_write"],
        },
    }


@router.get("/ai-provider")
async def get_ai_provider_status(
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Mevcut AI provider ayarı ve key durumu."""
    q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    return {
        "ai_provider": seller.ai_provider or "claude",
        "has_anthropic_key": bool(getattr(seller, "anthropic_api_key_enc", None)),
        "has_openai_key": bool(getattr(seller, "openai_api_key_enc", None)),
        "model_claude": "claude-sonnet-4-6",
        "model_openai": "gpt-4o",
        "features": {
            "tool_use": seller.ai_provider == "claude",
            "extended_thinking": seller.ai_provider == "claude",
            "prompt_caching": seller.ai_provider == "claude",
        },
    }
