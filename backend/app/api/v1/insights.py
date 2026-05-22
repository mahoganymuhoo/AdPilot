from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
from app.services.ml.lstm_anomaly import detect_anomalies
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


class AskRequest(BaseModel):
    question: str
    seller_id: int = 1
    product_id: int | None = None


async def _build_tool_executor(seller_id: int, db: AsyncSession):
    """
    Claude'un tool çağrılarını gerçek DB sorgularına yönlendiren executor fabrikası.
    Closure ile seller_id ve db session'ı yakalar.
    """
    async def execute(tool_name: str, tool_input: dict) -> dict:
        if tool_name == "get_roas_trend":
            pid = tool_input["product_id"]
            days = tool_input.get("days", 30)
            since = datetime.now(timezone.utc) - timedelta(days=days)
            q = await db.execute(
                select(AdMetric)
                .where(AdMetric.product_id == pid, AdMetric.time >= since)
                .order_by(AdMetric.time)
            )
            rows = q.scalars().all()
            if not rows:
                return {"error": "Veri bulunamadı", "product_id": pid}
            data = [{"date": str(m.time.date()), "roas": round(m.roas or 0, 3)} for m in rows]
            avg_roas = sum(d["roas"] for d in data) / len(data)
            recent_avg = sum(d["roas"] for d in data[-7:]) / len(data[-7:]) if len(data) >= 7 else avg_roas
            return {
                "product_id": pid,
                "days": days,
                "data_points": len(data),
                "avg_roas": round(avg_roas, 3),
                "recent_7d_avg_roas": round(recent_avg, 3),
                "trend": "improving" if recent_avg > avg_roas * 1.05 else "declining" if recent_avg < avg_roas * 0.95 else "stable",
                "daily": data[-14:],  # son 14 gün detay
            }

        elif tool_name == "get_product_metrics":
            pid = tool_input["product_id"]
            since = datetime.now(timezone.utc) - timedelta(days=30)
            q = await db.execute(
                select(AdMetric).where(AdMetric.product_id == pid, AdMetric.time >= since)
            )
            rows = q.scalars().all()
            pq = await db.execute(select(Product).where(Product.id == pid))
            product = pq.scalar_one_or_none()
            if not rows:
                return {"error": "Veri bulunamadı", "product_id": pid}
            revenue = sum(m.revenue for m in rows)
            spend = sum(m.ad_spend for m in rows)
            clicks = sum(m.clicks for m in rows)
            impressions = sum(getattr(m, "impressions", 0) or 0 for m in rows)
            conversions = sum(m.conversions for m in rows)
            roas = revenue / spend if spend > 0 else 0
            acos = spend / revenue * 100 if revenue > 0 else 0
            ctr = clicks / impressions * 100 if impressions > 0 else 0
            cogs = getattr(product, "cogs", None) or (revenue * 0.3)
            price = getattr(product, "price", None) or (revenue / max(conversions, 1))
            etsy_fee = price * 0.065 + 0.20
            break_even_acos = ((price - cogs - etsy_fee) / price * 100) if price > 0 else 0
            return {
                "product_id": pid,
                "title": getattr(product, "title", ""),
                "period_days": 30,
                "total_revenue": round(revenue, 2),
                "total_ad_spend": round(spend, 2),
                "total_conversions": conversions,
                "roas": round(roas, 3),
                "acos": round(acos, 2),
                "ctr_pct": round(ctr, 3),
                "cogs": round(cogs, 2),
                "price": round(price, 2),
                "break_even_acos": round(break_even_acos, 2),
                "is_profitable": acos < break_even_acos if break_even_acos > 0 else None,
            }

        elif tool_name == "get_anomalies":
            sid = tool_input.get("seller_id", seller_id)
            since = datetime.now(timezone.utc) - timedelta(days=7)
            from app.models.anomaly_log import AnomalyLog
            try:
                q = await db.execute(
                    select(AnomalyLog)
                    .where(AnomalyLog.seller_id == sid, AnomalyLog.detected_at >= since)
                    .order_by(AnomalyLog.detected_at.desc())
                    .limit(10)
                )
                anomalies = q.scalars().all()
                return {
                    "count": len(anomalies),
                    "anomalies": [
                        {
                            "metric": a.metric,
                            "z_score": round(a.z_score, 2),
                            "severity": a.severity,
                            "direction": a.direction,
                            "detected_at": str(a.detected_at),
                            "product_id": a.product_id,
                        }
                        for a in anomalies
                    ],
                }
            except Exception:
                return {"count": 0, "anomalies": [], "note": "Anomali tablosu henüz mevcut değil"}

        elif tool_name == "get_budget_allocation":
            sid = tool_input.get("seller_id", seller_id)
            since = datetime.now(timezone.utc) - timedelta(days=7)
            q = await db.execute(
                select(
                    AdMetric.product_id,
                    func.sum(AdMetric.ad_spend).label("total_spend"),
                    func.sum(AdMetric.revenue).label("total_revenue"),
                    func.avg(AdMetric.roas).label("avg_roas"),
                )
                .join(Product, Product.id == AdMetric.product_id)
                .where(Product.seller_id == sid, AdMetric.time >= since)
                .group_by(AdMetric.product_id)
                .order_by(func.sum(AdMetric.ad_spend).desc())
            )
            rows = q.all()
            total_spend = sum(r.total_spend or 0 for r in rows)
            return {
                "seller_id": sid,
                "period_days": 7,
                "total_spend": round(total_spend, 2),
                "allocations": [
                    {
                        "product_id": r.product_id,
                        "spend": round(r.total_spend or 0, 2),
                        "revenue": round(r.total_revenue or 0, 2),
                        "avg_roas": round(r.avg_roas or 0, 3),
                        "share_pct": round((r.total_spend or 0) / total_spend * 100, 1) if total_spend > 0 else 0,
                    }
                    for r in rows
                ],
            }

        elif tool_name == "get_strategy_history":
            sid = tool_input.get("seller_id", seller_id)
            pid = tool_input.get("product_id")
            from app.models.strategy import Strategy, StrategyOutcome
            q_base = select(Strategy).where(Strategy.seller_id == sid, Strategy.status == "completed")
            if pid:
                q_base = q_base.where(Strategy.product_id == pid)
            q = await db.execute(q_base.order_by(Strategy.created_at.desc()).limit(20))
            strategies = q.scalars().all()
            success = sum(1 for s in strategies if getattr(s, "outcome_summary", "") == "success")
            return {
                "total_strategies": len(strategies),
                "success_count": success,
                "success_rate_pct": round(success / len(strategies) * 100, 1) if strategies else 0,
                "recent": [
                    {
                        "id": s.id,
                        "operation_type": s.operation_type,
                        "status": s.status,
                        "timeline_days": s.timeline_days,
                        "created_at": str(s.created_at),
                    }
                    for s in strategies[:5]
                ],
            }

        return {"error": f"Bilinmeyen tool: {tool_name}"}

    return execute


@router.post("/ask")
async def ask_with_tools(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Claude'un tool use ile kendi veri sorgulayarak soruyu yanıtlaması.

    Claude hangi metriklere ihtiyaç duyduğuna kendisi karar verir,
    tool'lar aracılığıyla DB'yi sorgular ve kapsamlı analiz üretir.
    """
    seller_q = await db.execute(select(Seller).where(Seller.id == body.seller_id))
    seller = seller_q.scalar_one_or_none()
    if not seller:
        raise HTTPException(404, "Seller bulunamadı.")

    seller_context = _seller_context(seller)
    if body.product_id:
        seller_context["product_id"] = body.product_id

    provider = get_llm_provider(ai_provider=seller.ai_provider)
    tool_executor = await _build_tool_executor(body.seller_id, db)

    result = await provider.analyze_with_tools(
        question=body.question,
        seller_context=seller_context,
        tool_executor=tool_executor,
    )

    insight = AIInsight(
        product_id=body.product_id, seller_id=body.seller_id,
        insight_type="deep_analysis", ai_provider=result.provider,
        model_used=result.model, result_json=result.result_json,
        summary_text=result.summary_text, prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens, cache_hit=int(result.cache_hit),
    )
    db.add(insight)
    await db.commit()

    return {
        "question": body.question,
        "provider": result.provider,
        "model": result.model,
        "summary": result.summary_text,
        "findings": result.result_json.get("findings", []),
        "recommendation": result.result_json.get("recommendation", ""),
        "actions": result.result_json.get("actions", []),
        "watch_metrics": result.result_json.get("watch_metrics", []),
        "confidence": result.result_json.get("confidence", "medium"),
        "tools_used": result.result_json.get("tools_used", []),
        "tokens": {
            "prompt": result.prompt_tokens,
            "completion": result.completion_tokens,
            "cache_hit": result.cache_hit,
        },
    }


@router.get("/product/{product_id}/anomaly-detection")
async def get_anomaly_detection(
    product_id: int,
    metric: str = "roas",       # roas | acos | ctr
    days: int = 90,
    threshold: float = 2.5,
    db: AsyncSession = Depends(get_db),
):
    """
    Hibrit anomali tespiti: veri azsa Z-score, yeterliyse LSTM.

    metric: hangi metrik üzerinde anomali aranacak (roas/acos/ctr)
    days: kaç günlük veri kullanılacak
    threshold: anomali eşiği (sigma cinsinden, varsayılan 2.5)
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
        .order_by(AdMetric.time)
    )
    rows = q.scalars().all()

    if not rows:
        raise HTTPException(404, "Veri bulunamadı.")

    metric_map = {
        "roas": lambda m: m.roas or 0.0,
        "acos": lambda m: m.acos or 0.0,
        "ctr": lambda m: m.ctr or 0.0,
    }
    getter = metric_map.get(metric, metric_map["roas"])
    values = [getter(m) for m in rows]
    dates = [str(m.time.date()) for m in rows]

    result = detect_anomalies(values, threshold=threshold)

    return {
        "product_id": product_id,
        "metric": metric,
        "period_days": days,
        "series_length": result.series_length,
        "method_used": result.method_used,
        "threshold": threshold,
        "anomaly_count": result.anomaly_count,
        "summary": result.summary,
        "anomalies": [
            {
                "date": dates[a.index] if a.index < len(dates) else None,
                "index": a.index,
                "value": round(a.value, 3),
                "score": round(a.score, 3),
                "severity": a.severity,
                "direction": a.direction,
                "z_score": a.z_score,
                "lstm_error": a.lstm_error,
            }
            for a in result.anomalies
        ],
    }
