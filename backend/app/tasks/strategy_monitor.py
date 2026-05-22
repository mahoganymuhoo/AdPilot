"""
Celery görevi: Aktif stratejileri otomatik tara, checkpoint zamanı gelmişse
monitor_strategy çağır ve StrategyCheckpoint kaydı oluştur.
"""
from datetime import datetime, timedelta
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.core.database import SyncSession  # sync session for Celery
from app.models.strategy import Strategy, StrategyCheckpoint
from app.models.ad_metrics import AdMetrics
from app.services.llm.factory import get_llm_provider
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.strategy_monitor.check_active_strategies", bind=True, max_retries=3)
def check_active_strategies(self):
    """
    Her saat çalışır. Aktif stratejileri tarar:
    1. check_interval_days geçmişse ve son checkpoint o kadar eskiyse → yeni checkpoint al
    2. target_date geçmişse ve outcome yoksa → stratejiyi 'completed' yap (manuel verdict bekleniyor)
    """
    try:
        asyncio.run(_check_strategies())
    except Exception as exc:
        logger.error(f"Strategy monitor failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


async def _check_strategies():
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Strategy).where(Strategy.status.in_(["active", "monitoring"]))
        )
        strategies = result.scalars().all()
        logger.info(f"Checking {len(strategies)} active strategies")

        for strategy in strategies:
            await _process_strategy(db, strategy)

        await db.commit()


async def _process_strategy(db, strategy: Strategy):
    now = datetime.utcnow()

    # Süre dolmuş mu?
    if now > strategy.target_date and strategy.status != "completed":
        logger.info(f"Strategy {strategy.id} ({strategy.name}) — target date passed, awaiting verdict")
        strategy.status = "monitoring"  # verdict bekleniyor, kullanıcı manuel tamamlayacak
        return

    # Son checkpoint ne zaman alındı?
    result = await db.execute(
        select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy.id)
        .order_by(StrategyCheckpoint.checked_at.desc())
        .limit(1)
    )
    last_checkpoint = result.scalar_one_or_none()

    if last_checkpoint:
        next_check = last_checkpoint.checked_at + timedelta(days=strategy.check_interval_days)
    else:
        # İlk checkpoint: başlangıçtan check_interval_days sonra
        next_check = strategy.initiated_at + timedelta(days=strategy.check_interval_days)

    if now < next_check:
        return  # Henüz zamanı gelmedi

    logger.info(f"Strategy {strategy.id} — taking checkpoint (day {(now - strategy.initiated_at).days})")
    await _take_checkpoint(db, strategy)


async def _take_checkpoint(db, strategy: Strategy):
    from sqlalchemy import select as sa_select
    from app.models.ad_metrics import AdMetrics
    from app.models.seller import Seller

    now = datetime.utcnow()
    days_elapsed = (now - strategy.initiated_at).days
    days_remaining = max(0, (strategy.target_date - now).days)

    # Son 7 günün ortalama metriklerini çek
    since = now - timedelta(days=7)
    metrics_result = await db.execute(
        sa_select(AdMetrics)
        .where(AdMetrics.product_id == strategy.product_id)
        .where(AdMetrics.time >= since)
        .order_by(AdMetrics.time.desc())
    )
    recent_metrics = metrics_result.scalars().all()

    if not recent_metrics:
        logger.warning(f"Strategy {strategy.id} — no recent metrics, skipping checkpoint")
        return

    # Metrik ortalaması
    current_metrics = {
        "roas": round(sum(m.roas for m in recent_metrics) / len(recent_metrics), 2),
        "acos": round(sum(m.acos for m in recent_metrics) / len(recent_metrics), 2),
        "ad_spend": round(sum(m.ad_spend for m in recent_metrics), 2),
        "revenue": round(sum(m.revenue for m in recent_metrics), 2),
        "ctr": round(sum(m.ctr for m in recent_metrics) / len(recent_metrics), 4),
        "conversions": sum(m.conversions for m in recent_metrics),
        "daily_revenue": round(sum(m.revenue for m in recent_metrics) / 7, 2),
        "data_points": len(recent_metrics),
    }

    # Tüm önceki checkpoint'leri context olarak topla
    cp_result = await db.execute(
        sa_select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy.id)
        .order_by(StrategyCheckpoint.checked_at)
    )
    existing_checkpoints = cp_result.scalars().all()

    strategy_ctx = {
        "name": strategy.name,
        "operation_type": strategy.operation_type,
        "initial_metrics": strategy.initial_metrics,
        "target_metrics": strategy.target_metrics,
        "success_criteria": strategy.ai_launch_analysis.get("success_criteria", []) if strategy.ai_launch_analysis else [],
        "goal_summary": strategy.ai_launch_analysis.get("goal_summary", "") if strategy.ai_launch_analysis else "",
        "timeline_days": (strategy.target_date - strategy.initiated_at).days,
    }

    checkpoints_ctx = [
        {
            "checked_at": cp.checked_at.isoformat(),
            "metrics": cp.current_metrics,
            "status": cp.status,
            "progress_pct": cp.progress_pct,
            "insight": cp.ai_analysis.get("checkpoint_insight", "") if cp.ai_analysis else "",
            "seller_note": cp.seller_note,
        }
        for cp in existing_checkpoints
    ]

    # Seller'ın AI provider ve key'ini bul
    seller_result = await db.execute(
        sa_select(Seller).where(Seller.id == strategy.seller_id)
    )
    seller = seller_result.scalar_one_or_none()
    ai_provider = seller.ai_provider if seller else "claude"
    # TODO: decrypt api_key_enc when encryption is implemented
    api_key = None

    # AI çağrısı
    try:
        llm = get_llm_provider(ai_provider, api_key)
        result = await llm.monitor_strategy(
            strategy=strategy_ctx,
            checkpoints=checkpoints_ctx,
            current_metrics=current_metrics,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
        )
        r = result.result_json
    except Exception as e:
        logger.error(f"LLM call failed for strategy {strategy.id}: {e}")
        # AI olmadan da checkpoint yaz (metrikleri kaydet, AI analizi boş)
        r = {
            "status": "unknown",
            "progress_pct": 0,
            "checkpoint_insight": f"AI analizi yapılamadı: {str(e)}",
            "red_flags": [],
            "metric_deltas": {},
        }

    checkpoint = StrategyCheckpoint(
        strategy_id=strategy.id,
        current_metrics=current_metrics,
        ai_analysis=r,
        progress_pct=r.get("progress_pct", 0.0),
        status=r.get("status", "unknown"),
    )
    db.add(checkpoint)

    # off_track ise strateji durumunu güncelle
    if r.get("status") == "off_track":
        strategy.status = "monitoring"

    logger.info(
        f"Strategy {strategy.id} checkpoint saved — status: {r.get('status')}, "
        f"progress: {r.get('progress_pct')}%"
    )
