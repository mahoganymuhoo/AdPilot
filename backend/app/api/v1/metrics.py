from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.models.ad_metrics import AdMetric
from app.models.product import Product
from app.services.analytics import (
    calculate_profitability, analyze_trend, detect_anomaly, calculate_ad_worthiness,
    calculate_dayparting,
)
from app.services.data_import import parse_etsy_stats_csv, parse_manual_entries
from app.schemas.metrics import ManualMetricEntry, MetricsRead, ProfitabilityResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    platform_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Etsy CSV export dosyasını yükle ve veritabanına kaydet."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Sadece .csv dosyası kabul edilir.")

    content = await file.read()
    rows = parse_etsy_stats_csv(content)

    if not rows:
        raise HTTPException(422, "CSV'den geçerli veri okunamadı. Etsy stats export formatını kontrol edin.")

    saved_count = 0
    for row in rows:
        # Ürünü bul veya oluştur
        product_q = await db.execute(
            select(Product).where(Product.listing_id == row.listing_id)
        )
        product = product_q.scalar_one_or_none()

        if not product:
            product = Product(
                seller_id=1,  # TODO: JWT'den al
                platform_id=platform_id,
                listing_id=row.listing_id,
                title=row.title,
            )
            db.add(product)
            await db.flush()

        roas = row.revenue / row.ad_spend if row.ad_spend > 0 else None
        acos = (row.ad_spend / row.revenue * 100) if row.revenue > 0 else None
        ctr = (row.clicks / row.impressions * 100) if row.impressions > 0 else None
        cvr = (row.conversions / row.clicks * 100) if row.clicks > 0 else None
        cpc = (row.ad_spend / row.clicks) if row.clicks > 0 else None

        metric = AdMetric(
            time=row.date,
            product_id=product.id,
            platform_id=platform_id,
            impressions=row.impressions,
            clicks=row.clicks,
            ad_spend=row.ad_spend,
            revenue=row.revenue,
            conversions=row.conversions,
            views=row.views,
            roas=roas,
            acos=acos,
            ctr=ctr,
            conversion_rate=cvr,
            cpc=cpc,
            data_source="csv",
        )
        db.add(metric)
        saved_count += 1

    await db.commit()
    return {"message": f"{saved_count} metrik kaydedildi.", "rows_parsed": len(rows)}


@router.post("/manual")
async def add_manual_metrics(
    entries: list[ManualMetricEntry],
    platform_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Manuel form girişi ile metrik ekle."""
    rows = parse_manual_entries([e.model_dump() for e in entries])
    saved = 0

    for row in rows:
        product_q = await db.execute(
            select(Product).where(Product.listing_id == row.listing_id)
        )
        product = product_q.scalar_one_or_none()

        if not product:
            product = Product(
                seller_id=1,  # TODO: JWT
                platform_id=platform_id,
                listing_id=row.listing_id,
                title=row.title or "Manuel Ürün",
            )
            db.add(product)
            await db.flush()

        metric = AdMetric(
            time=row.date,
            product_id=product.id,
            platform_id=platform_id,
            impressions=row.impressions,
            clicks=row.clicks,
            ad_spend=row.ad_spend,
            revenue=row.revenue,
            conversions=row.conversions,
            views=row.views,
            roas=row.revenue / row.ad_spend if row.ad_spend > 0 else None,
            acos=(row.ad_spend / row.revenue * 100) if row.revenue > 0 else None,
            ctr=(row.clicks / row.impressions * 100) if row.impressions > 0 else None,
            conversion_rate=(row.conversions / row.clicks * 100) if row.clicks > 0 else None,
            data_source="manual",
        )
        db.add(metric)
        saved += 1

    await db.commit()
    return {"message": f"{saved} metrik kaydedildi."}


@router.get("/product/{product_id}/profitability", response_model=ProfitabilityResponse)
async def get_product_profitability(
    product_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Ürün için son N günlük kârlılık analizi döndürür."""
    product_q = await db.execute(select(Product).where(Product.id == product_id))
    product = product_q.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Ürün bulunamadı.")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    metrics_q = await db.execute(
        select(AdMetric)
        .where(AdMetric.product_id == product_id, AdMetric.time >= since)
        .order_by(AdMetric.time)
    )
    metrics = metrics_q.scalars().all()

    if not metrics:
        raise HTTPException(404, "Bu ürün için yeterli metrik verisi yok.")

    total_revenue = sum(m.revenue for m in metrics)
    total_ad_spend = sum(m.ad_spend for m in metrics)
    total_conversions = sum(m.conversions for m in metrics)

    cogs = product.cogs or (total_revenue * 0.40)
    shipping = product.shipping_cost or 0.0

    profitability = calculate_profitability(
        revenue=total_revenue,
        ad_spend=total_ad_spend,
        total_revenue=total_revenue,
        cogs=cogs,
        shipping_cost=shipping,
        price=product.price,
    )

    daily_roas = [m.roas or 0.0 for m in metrics]
    trend = analyze_trend(daily_roas)

    anomalies = []
    if len(daily_roas) >= 5:
        for metric_name, values in [
            ("roas", daily_roas),
            ("acos", [m.acos or 0.0 for m in metrics]),
            ("ctr", [m.ctr or 0.0 for m in metrics]),
        ]:
            result = detect_anomaly(metric_name, values[-1], values[:-1])
            if result.is_anomaly:
                anomalies.append({
                    "metric": result.metric_name,
                    "severity": result.severity,
                    "direction": result.direction,
                    "message": result.message,
                    "z_score": result.z_score,
                })

    return ProfitabilityResponse(
        product_id=product_id,
        product_title=product.title,
        roas=profitability.roas,
        acos=profitability.acos,
        tacos=profitability.tacos,
        break_even_acos=profitability.break_even_acos,
        net_profit_per_sale=profitability.net_profit_per_sale,
        is_profitable=profitability.is_profitable,
        profit_margin=profitability.profit_margin,
        recommendation=profitability.recommendation,
        budget_change_pct=profitability.budget_change_pct,
        ema_7d=trend.ema_7d,
        ema_30d=trend.ema_30d,
        trend=trend.trend,
        anomalies=anomalies,
    )


@router.get("/product/{product_id}/dayparting")
async def get_dayparting(
    product_id: int,
    days: int = 90,
    db: AsyncSession = Depends(get_db),
):
    """
    Saat × gün ısı haritası verisi.
    En verimli reklam zamanlarını ROAS ve CTR bazında gösterir.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # PostgreSQL EXTRACT ile saatlik/günlük aggregation
    result = await db.execute(
        text("""
            SELECT
                EXTRACT(hour FROM time AT TIME ZONE 'UTC')::int AS hour,
                EXTRACT(isodow FROM time AT TIME ZONE 'UTC')::int - 1 AS dow,
                AVG(CASE WHEN impressions > 0 THEN clicks::float / impressions ELSE 0 END) AS ctr,
                AVG(CASE WHEN ad_spend > 0 THEN revenue / ad_spend ELSE 0 END) AS roas,
                AVG(ad_spend) AS ad_spend,
                COUNT(*) AS data_points
            FROM ad_metrics
            WHERE product_id = :pid AND time >= :since
              AND ad_spend > 0
            GROUP BY hour, dow
            ORDER BY hour, dow
        """),
        {"pid": product_id, "since": since},
    )
    rows = result.mappings().all()

    metrics_with_time = [
        {
            "hour": row["hour"],
            "dow": row["dow"],
            "ctr": float(row["ctr"] or 0),
            "roas": float(row["roas"] or 0),
            "ad_spend": float(row["ad_spend"] or 0),
        }
        for row in rows
    ]

    dp = calculate_dayparting(metrics_with_time)

    return {
        "product_id": product_id,
        "period_days": days,
        "data_points": len(rows),
        "cells": [
            {
                "hour": c.hour,
                "dow": c.dow,
                "avg_ctr": c.avg_ctr,
                "avg_roas": c.avg_roas,
                "avg_spend": c.avg_spend,
                "n": c.data_points,
            }
            for c in dp.cells
        ],
        "best_hours": dp.best_hours,
        "best_days": dp.best_days,
        "worst_hours": dp.worst_hours,
        "peak_cell": {
            "hour": dp.peak_cell.hour,
            "dow": dp.peak_cell.dow,
            "avg_roas": dp.peak_cell.avg_roas,
        } if dp.peak_cell else None,
        "recommendation": dp.recommendation,
        "dow_labels": dp.dow_labels,
    }
