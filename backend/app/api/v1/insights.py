from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.models.ad_metrics import AdMetric
from app.models.product import Product
from app.models.seller import Seller
from app.models.ai_insight import AIInsight
from app.services.analytics import (
    calculate_ad_worthiness, optimize_budget,
    calculate_saturation_curve, stress_test_breakeven,
    calculate_listing_quality, detect_product_lifecycle,
)
from app.services.llm import get_llm_provider
from app.schemas.insights import InsightResponse, AdWorthinessResponse, BudgetRecommendationResponse

router = APIRouter(prefix="/insights", tags=["insights"])


def _seller_context(seller: Seller) -> dict:
    return {
        "target_roas": seller.target_roas,
        "target_acos": seller.target_acos,
        "daily_budget": seller.daily_budget,
        "default_cogs_percent": seller.default_cogs_percent,
    }


@router.get("/product/{product_id}/ad-worthiness", response_model=AdWorthinessResponse)
async def get_ad_worthiness(
    product_id: int,
    seller_id: int = 1,  # TODO: JWT'den al
    db: AsyncSession = Depends(get_db),
):
    """Ürün için 'Reklam verilmeli mi?' skorunu hesapla ve AI ile yorumla."""
    product_q = await db.execute(select(Product).where(Product.id == product_id))
    product = product_q.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Ürün bulunamadı.")

    seller_q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=30)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
        .order_by(AdMetric.time)
    )
    metrics = list(metrics_q.scalars().all())

    views_30d = sum(m.views for m in metrics)
    sales_30d = sum(m.conversions for m in metrics)
    total_revenue = sum(m.revenue for m in metrics)
    total_ad_spend = sum(m.ad_spend for m in metrics)
    cogs = product.cogs or (total_revenue * seller.default_cogs_percent)
    profit_margin = max(0.0, (total_revenue - cogs - total_ad_spend) / max(total_revenue, 0.01))

    daily_roas = [m.roas or 0.0 for m in metrics]
    from app.services.analytics import analyze_trend
    trend = analyze_trend(daily_roas)

    worthiness = calculate_ad_worthiness(
        views_30d=views_30d,
        sales_30d=sales_30d,
        profit_margin=profit_margin,
        inventory=product.inventory,
        roas_trend=trend.trend,
    )

    # AI analizi
    product_metrics = {
        "views_30d": views_30d, "sales_30d": sales_30d,
        "revenue_30d": total_revenue, "ad_spend_30d": total_ad_spend,
        "profit_margin": profit_margin, "inventory": product.inventory,
        "roas_trend": trend.trend, "algorithmic_score": worthiness.score,
    }

    try:
        provider = get_llm_provider(
            ai_provider=seller.ai_provider,
            api_key=seller.anthropic_api_key_enc or seller.openai_api_key_enc,
        )
        ai_result = await provider.score_ad_worthiness(product_metrics, _seller_context(seller))
        ai_analysis = ai_result.result_json

        insight = AIInsight(
            product_id=product_id, seller_id=seller_id,
            insight_type="ad_worthiness", ai_provider=ai_result.provider,
            model_used=ai_result.model, result_json=ai_result.result_json,
            summary_text=ai_result.summary_text, prompt_tokens=ai_result.prompt_tokens,
            completion_tokens=ai_result.completion_tokens, cache_hit=int(ai_result.cache_hit),
        )
        db.add(insight)
        await db.commit()
    except Exception as e:
        ai_analysis = {"error": str(e), "note": "AI analizi başarısız, algoritma skoru geçerli."}

    return AdWorthinessResponse(
        product_id=product_id,
        product_title=product.title,
        score=worthiness.score,
        recommendation=worthiness.recommendation,
        view_situation=worthiness.view_situation,
        view_diagnosis=worthiness.view_diagnosis,
        pre_ad_action=worthiness.pre_ad_action,
        reasons=worthiness.reasons,
        suggested_daily_budget=worthiness.suggested_daily_budget,
        ai_analysis=ai_analysis,
    )


@router.post("/budget-recommendation", response_model=BudgetRecommendationResponse)
async def get_budget_recommendation(
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Tüm ürünler için bütçe dağılımı önerisi."""
    seller_q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    products_q = await db.execute(
        select(Product).where(Product.seller_id == seller_id, Product.is_active == True)
    )
    products = list(products_q.scalars().all())

    since = datetime.now(timezone.utc) - timedelta(days=14)
    product_data = []
    for p in products:
        metrics_q = await db.execute(
            select(AdMetric)
            .where(AdMetric.product_id == p.id, AdMetric.time >= since)
        )
        metrics = list(metrics_q.scalars().all())
        if not metrics:
            continue
        total_rev = sum(m.revenue for m in metrics)
        total_spend = sum(m.ad_spend for m in metrics)
        roas = total_rev / total_spend if total_spend > 0 else 0.0
        product_data.append({
            "id": p.id, "title": p.title,
            "roas": round(roas, 2),
            "current_budget": seller.daily_budget / max(len(products), 1),
        })

    allocations = optimize_budget(product_data, seller.daily_budget)

    try:
        provider = get_llm_provider(ai_provider=seller.ai_provider)
        ai_result = await provider.generate_budget_recommendation(product_data, seller.daily_budget)
        ai_analysis = ai_result.result_json
        strategy_summary = ai_result.result_json.get("strategy_summary", "")
        paused = ai_result.result_json.get("paused_products", [])
    except Exception as e:
        ai_analysis = {"error": str(e)}
        strategy_summary = "Algoritma bazlı optimizasyon uygulandı."
        paused = [a.product_title for a in allocations if a.suggested_budget == 0.0]

    return BudgetRecommendationResponse(
        total_budget=seller.daily_budget,
        allocations=[
            {
                "product_id": a.product_id,
                "product_title": a.product_title,
                "current_budget": a.current_budget,
                "suggested_budget": a.suggested_budget,
                "roas": a.roas,
                "reason": a.reason,
            }
            for a in allocations
        ],
        paused_products=paused,
        strategy_summary=strategy_summary,
        ai_analysis=ai_analysis,
    )


@router.get("/product/{product_id}/listing-quality")
async def get_listing_quality(
    product_id: int,
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Listing kalite skoru: CTR / kategori benchmark karşılaştırması."""
    product_q = await db.execute(select(Product).where(Product.id == product_id))
    product = product_q.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Ürün bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=30)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
    )
    metrics = list(metrics_q.scalars().all())

    total_impressions = sum(getattr(m, "impressions", 0) or 0 for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    product_ctr = total_clicks / total_impressions if total_impressions > 0 else 0.018

    category = getattr(product, "category", "default") or "default"

    result = calculate_listing_quality(
        product_ctr=product_ctr,
        category=category,
        image_count=getattr(product, "image_count", 1) or 1,
        has_video=getattr(product, "has_video", False) or False,
        review_count=getattr(product, "review_count", 0) or 0,
        avg_rating=getattr(product, "avg_rating", 0.0) or 0.0,
    )

    return {
        "product_id": product_id,
        "score": result.score,
        "grade": result.grade,
        "ctr_ratio": result.ctr_ratio,
        "product_ctr_pct": round(result.product_ctr * 100, 2),
        "category_avg_ctr_pct": round(result.category_avg_ctr * 100, 2),
        "category": result.category,
        "recommendation": result.recommendation,
        "issues": result.issues,
        "strengths": result.strengths,
    }


@router.get("/product/{product_id}/lifecycle")
async def get_product_lifecycle(
    product_id: int,
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Ürün yaşam döngüsü evresi: launch / growth / mature / declining."""
    since = datetime.now(timezone.utc) - timedelta(days=90)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
        .order_by(AdMetric.time)
    )
    metrics = list(metrics_q.scalars().all())
    roas_history = [m.roas or 0.0 for m in metrics]

    result = detect_product_lifecycle(roas_history=roas_history)

    return {
        "product_id": product_id,
        "stage": result.stage,
        "label": result.label,
        "confidence": result.confidence,
        "roas_trend_pct": result.roas_trend_pct,
        "ema_7d": result.ema_7d,
        "ema_30d": result.ema_30d,
        "days_with_data": result.days_with_data,
        "recommendation": result.recommendation,
        "next_action": result.next_action,
    }


@router.get("/product/{product_id}/saturation-curve")
async def get_saturation_curve(
    product_id: int,
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    Bütçe → ROAS eğrisi. "Daha fazla harcasam ne olur?" sorusunu cevaplar.
    """
    seller_q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=90)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
        .order_by(AdMetric.time)
    )
    metrics = list(metrics_q.scalars().all())

    # Haftalık gruplar halinde (bütçe, ROAS) çiftleri oluştur
    history: list[dict] = []
    for m in metrics:
        if m.ad_spend and m.ad_spend > 0 and m.roas and m.roas > 0:
            history.append({"budget": round(m.ad_spend, 2), "roas": round(m.roas, 3)})

    current_budget = seller.daily_budget / max(1, 1)

    result = calculate_saturation_curve(
        budget_roas_history=history,
        current_budget=current_budget,
    )

    return {
        "product_id": product_id,
        "current_budget": current_budget,
        "curve_points": result.curve_points,
        "optimal_budget": result.optimal_budget,
        "current_efficiency_pct": result.current_efficiency_pct,
        "diminishing_return_budget": result.diminishing_return_budget,
        "recommendation": result.recommendation,
        "data_points_used": len(history),
    }


@router.get("/product/{product_id}/stress-test")
async def get_stress_test(
    product_id: int,
    seller_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """
    COGS değişim senaryolarında karlılık simülasyonu.
    """
    product_q = await db.execute(select(Product).where(Product.id == product_id))
    product = product_q.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Ürün bulunamadı.")

    seller_q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=30)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
    )
    metrics = list(metrics_q.scalars().all())

    total_revenue = sum(m.revenue for m in metrics)
    total_ad_spend = sum(m.ad_spend for m in metrics)
    current_acos = (total_ad_spend / total_revenue * 100) if total_revenue > 0 else 50.0

    price = product.price or (total_revenue / max(sum(m.conversions for m in metrics), 1))
    cogs = product.cogs or (price * 0.3)
    shipping = product.shipping_cost or 0.0

    result = stress_test_breakeven(
        price=price,
        cogs=cogs,
        shipping_cost=shipping,
        current_acos=current_acos,
    )

    return {
        "product_id": product_id,
        "price": round(price, 2),
        "current_cogs": round(cogs, 2),
        "current_acos": round(current_acos, 2),
        "base_break_even_acos": result.base_break_even_acos,
        "base_net_profit": result.base_net_profit,
        "safe_up_to_cogs_increase": result.safe_up_to_cogs_increase,
        "scenarios": [
            {
                "label": s.label,
                "cogs_change_pct": s.cogs_change_pct,
                "new_cogs": s.new_cogs,
                "new_break_even_acos": s.new_break_even_acos,
                "new_net_profit": s.new_net_profit,
                "is_still_profitable": s.is_still_profitable,
                "margin_change_pts": s.margin_change_pts,
            }
            for s in result.scenarios
        ],
    }


@router.get("/product/{product_id}/profitability-ai", response_model=InsightResponse)
async def get_profitability_ai(
    product_id: int,
    seller_id: int = 1,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """AI ile kârlılık yorumu al."""
    seller_q = await db.execute(select(Seller).where(Seller.id == seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    product_q = await db.execute(select(Product).where(Product.id == product_id))
    product = product_q.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Ürün bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
    )
    metrics = list(metrics_q.scalars().all())

    total_revenue = sum(m.revenue for m in metrics)
    total_ad_spend = sum(m.ad_spend for m in metrics)
    cogs = product.cogs or (total_revenue * seller.default_cogs_percent)

    metrics_payload = {
        "period_days": days,
        "total_revenue": total_revenue,
        "total_ad_spend": total_ad_spend,
        "total_conversions": sum(m.conversions for m in metrics),
        "avg_roas": total_revenue / total_ad_spend if total_ad_spend > 0 else 0,
        "cogs": cogs,
        "shipping_cost": product.shipping_cost,
        "price": product.price,
    }

    provider = get_llm_provider(ai_provider=seller.ai_provider)
    result = await provider.analyze_profitability(metrics_payload, _seller_context(seller))

    insight = AIInsight(
        product_id=product_id, seller_id=seller_id,
        insight_type="profitability", ai_provider=result.provider,
        model_used=result.model, result_json=result.result_json,
        summary_text=result.summary_text, prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens, cache_hit=int(result.cache_hit),
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)

    return InsightResponse(
        id=insight.id, product_id=product_id,
        insight_type=result.insight_type, ai_provider=result.provider,
        model_used=result.model, result_json=result.result_json,
        summary_text=result.summary_text, prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens, cache_hit=result.cache_hit,
    )
