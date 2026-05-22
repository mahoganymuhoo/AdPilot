from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.models.strategy import Strategy, StrategyCheckpoint, StrategyOutcome
from app.services.llm.factory import get_llm_provider
from app.services.analytics import project_strategy_outcome

router = APIRouter(prefix="/strategies", tags=["strategies"])


class LaunchStrategyRequest(BaseModel):
    seller_id: int
    product_id: int
    recommendation: dict
    initial_metrics: dict
    seller_context: dict
    action_confirmed: str
    ai_provider: str = "claude"
    api_key: str | None = None


class CheckpointRequest(BaseModel):
    current_metrics: dict
    ai_provider: str = "claude"
    api_key: str | None = None


class VerdictRequest(BaseModel):
    final_metrics: dict
    ai_provider: str = "claude"
    api_key: str | None = None


@router.post("/launch")
async def launch_strategy(req: LaunchStrategyRequest, db: AsyncSession = Depends(get_db)):
    """
    Satıcı bir öneriyi uyguladı. AI hedef, takvim ve başarı kriterlerini belirler.
    Strategy kaydı oluşturulur.
    """
    llm = get_llm_provider(req.ai_provider, req.api_key)
    result = await llm.launch_strategy(
        recommendation=req.recommendation,
        initial_metrics=req.initial_metrics,
        seller_context=req.seller_context,
        action_confirmed=req.action_confirmed,
    )

    r = result.result_json
    timeline_days = r.get("timeline_days", 14)
    target_date = datetime.utcnow() + timedelta(days=timeline_days)

    strategy = Strategy(
        seller_id=req.seller_id,
        product_id=req.product_id,
        name=r.get("strategy_name", "Strateji"),
        operation_type=r.get("operation_type", "unknown"),
        status="active",
        target_date=target_date,
        initial_metrics=req.initial_metrics,
        target_metrics=r.get("target_metrics", {}),
        ai_launch_analysis=r,
        check_interval_days=r.get("check_interval_days", 3),
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)

    return {
        "strategy_id": strategy.id,
        "name": strategy.name,
        "operation_type": strategy.operation_type,
        "goal_summary": r.get("goal_summary"),
        "target_metrics": strategy.target_metrics,
        "timeline_days": timeline_days,
        "target_date": target_date.isoformat(),
        "check_interval_days": strategy.check_interval_days,
        "success_criteria": r.get("success_criteria", []),
        "watch_metrics": r.get("watch_metrics", []),
        "risk_factors": r.get("risk_factors", []),
        "confidence": r.get("confidence"),
        "action_assessment": r.get("action_assessment"),
        "reasoning": r.get("reasoning"),
        "ai_provider": result.provider,
        "tokens_used": result.prompt_tokens + result.completion_tokens,
    }


@router.get("/")
async def list_strategies(seller_id: int, db: AsyncSession = Depends(get_db)):
    """Satıcının tüm stratejilerini döndürür (aktif + tamamlanmış)."""
    result = await db.execute(
        select(Strategy).where(Strategy.seller_id == seller_id).order_by(Strategy.initiated_at.desc())
    )
    strategies = result.scalars().all()

    items = []
    for s in strategies:
        checkpoint_result = await db.execute(
            select(StrategyCheckpoint)
            .where(StrategyCheckpoint.strategy_id == s.id)
            .order_by(StrategyCheckpoint.checked_at.desc())
        )
        checkpoints = checkpoint_result.scalars().all()

        days_elapsed = (datetime.utcnow() - s.initiated_at).days
        days_remaining = max(0, (s.target_date - datetime.utcnow()).days)

        latest_status = checkpoints[0].status if checkpoints else "pending"
        latest_progress = checkpoints[0].progress_pct if checkpoints else 0.0

        items.append({
            "id": s.id,
            "name": s.name,
            "operation_type": s.operation_type,
            "status": s.status,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "target_date": s.target_date.isoformat(),
            "initial_metrics": s.initial_metrics,
            "target_metrics": s.target_metrics,
            "checkpoint_count": len(checkpoints),
            "latest_status": latest_status,
            "latest_progress_pct": latest_progress,
            "goal_summary": s.ai_launch_analysis.get("goal_summary") if s.ai_launch_analysis else None,
        })

    return {"strategies": items, "total": len(items)}


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Strateji detayı: tüm checkpoint'ler ve outcome dahil."""
    s = await db.get(Strategy, strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")

    checkpoint_result = await db.execute(
        select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy_id)
        .order_by(StrategyCheckpoint.checked_at)
    )
    checkpoints = checkpoint_result.scalars().all()

    outcome = await db.get(StrategyOutcome, strategy_id)

    return {
        "strategy": {
            "id": s.id,
            "name": s.name,
            "operation_type": s.operation_type,
            "status": s.status,
            "initiated_at": s.initiated_at.isoformat(),
            "target_date": s.target_date.isoformat(),
            "initial_metrics": s.initial_metrics,
            "target_metrics": s.target_metrics,
            "launch_analysis": s.ai_launch_analysis,
        },
        "checkpoints": [
            {
                "id": cp.id,
                "checked_at": cp.checked_at.isoformat(),
                "current_metrics": cp.current_metrics,
                "ai_analysis": cp.ai_analysis,
                "progress_pct": cp.progress_pct,
                "status": cp.status,
            }
            for cp in checkpoints
        ],
        "outcome": {
            "outcome": outcome.outcome,
            "completed_at": outcome.completed_at.isoformat(),
            "final_metrics": outcome.final_metrics,
            "ai_verdict": outcome.ai_verdict,
            "lessons_learned": outcome.lessons_learned,
            "next_strategy_hints": outcome.next_strategy_hints,
        } if outcome else None,
    }


@router.post("/{strategy_id}/checkpoint")
async def add_checkpoint(
    strategy_id: int,
    req: CheckpointRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Takip noktası ekle. AI mevcut metrikleri strateji hedefleriyle karşılaştırır.
    Checkpoint history'si context olarak gönderilir — AI geçmişi görür.
    """
    s = await db.get(Strategy, strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if s.status == "completed":
        raise HTTPException(status_code=400, detail="Strategy already completed")

    checkpoint_result = await db.execute(
        select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy_id)
        .order_by(StrategyCheckpoint.checked_at)
    )
    existing_checkpoints = checkpoint_result.scalars().all()

    days_elapsed = (datetime.utcnow() - s.initiated_at).days
    days_remaining = max(0, (s.target_date - datetime.utcnow()).days)

    strategy_ctx = {
        "name": s.name,
        "operation_type": s.operation_type,
        "initial_metrics": s.initial_metrics,
        "target_metrics": s.target_metrics,
        "success_criteria": s.ai_launch_analysis.get("success_criteria", []) if s.ai_launch_analysis else [],
        "goal_summary": s.ai_launch_analysis.get("goal_summary", "") if s.ai_launch_analysis else "",
        "timeline_days": (s.target_date - s.initiated_at).days,
    }

    checkpoints_ctx = [
        {
            "checked_at": cp.checked_at.isoformat(),
            "metrics": cp.current_metrics,
            "status": cp.status,
            "progress_pct": cp.progress_pct,
            "insight": cp.ai_analysis.get("checkpoint_insight", "") if cp.ai_analysis else "",
        }
        for cp in existing_checkpoints
    ]

    llm = get_llm_provider(req.ai_provider, req.api_key)
    result = await llm.monitor_strategy(
        strategy=strategy_ctx,
        checkpoints=checkpoints_ctx,
        current_metrics=req.current_metrics,
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
    )

    r = result.result_json
    checkpoint = StrategyCheckpoint(
        strategy_id=strategy_id,
        current_metrics=req.current_metrics,
        ai_analysis=r,
        progress_pct=r.get("progress_pct", 0.0),
        status=r.get("status", "unknown"),
    )
    db.add(checkpoint)

    if r.get("status") == "off_track":
        s.status = "monitoring"

    await db.commit()
    await db.refresh(checkpoint)

    return {
        "checkpoint_id": checkpoint.id,
        "status": r.get("status"),
        "progress_pct": r.get("progress_pct"),
        "trend": r.get("trend"),
        "milestone_hit": r.get("milestone_hit"),
        "adjustment_needed": r.get("adjustment_needed"),
        "adjustment": r.get("adjustment"),
        "checkpoint_insight": r.get("checkpoint_insight"),
        "red_flags": r.get("red_flags", []),
        "next_checkpoint_focus": r.get("next_checkpoint_focus"),
        "metric_deltas": r.get("metric_deltas"),
        "reasoning": r.get("reasoning"),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "ai_provider": result.provider,
        "tokens_used": result.prompt_tokens + result.completion_tokens,
    }


@router.post("/{strategy_id}/verdict")
async def complete_strategy(
    strategy_id: int,
    req: VerdictRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Strateji tamamlandı. AI tüm süreci değerlendirir, hedeflere ulaşıldı mı karar verir.
    Öğrenilenleri ve bir sonraki strateji için hint'leri DB'ye kaydeder.
    """
    s = await db.get(Strategy, strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")

    checkpoint_result = await db.execute(
        select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy_id)
        .order_by(StrategyCheckpoint.checked_at)
    )
    checkpoints = checkpoint_result.scalars().all()

    strategy_ctx = {
        "name": s.name,
        "operation_type": s.operation_type,
        "initial_metrics": s.initial_metrics,
        "target_metrics": s.target_metrics,
        "success_criteria": s.ai_launch_analysis.get("success_criteria", []) if s.ai_launch_analysis else [],
        "goal_summary": s.ai_launch_analysis.get("goal_summary", "") if s.ai_launch_analysis else "",
        "initiated_at": s.initiated_at.isoformat(),
        "target_date": s.target_date.isoformat(),
    }

    checkpoints_ctx = [
        {
            "checked_at": cp.checked_at.isoformat(),
            "metrics": cp.current_metrics,
            "status": cp.status,
            "progress_pct": cp.progress_pct,
            "ai_insight": cp.ai_analysis.get("checkpoint_insight", "") if cp.ai_analysis else "",
            "adjustment": cp.ai_analysis.get("adjustment") if cp.ai_analysis else None,
        }
        for cp in checkpoints
    ]

    llm = get_llm_provider(req.ai_provider, req.api_key)
    result = await llm.verdict_strategy(
        strategy=strategy_ctx,
        checkpoints=checkpoints_ctx,
        final_metrics=req.final_metrics,
    )

    r = result.result_json

    outcome = StrategyOutcome(
        strategy_id=strategy_id,
        outcome=r.get("outcome", "failed"),
        final_metrics=req.final_metrics,
        ai_verdict=r,
        lessons_learned=r.get("lessons_learned", []),
        next_strategy_hints=r.get("next_strategy_hints"),
    )
    db.add(outcome)
    s.status = "completed"
    await db.commit()

    return {
        "outcome": r.get("outcome"),
        "outcome_summary": r.get("outcome_summary"),
        "metric_results": r.get("metric_results"),
        "success_criteria_results": r.get("success_criteria_results", []),
        "what_worked": r.get("what_worked", []),
        "what_failed": r.get("what_failed", []),
        "lessons_learned": r.get("lessons_learned", []),
        "next_strategy_hints": r.get("next_strategy_hints"),
        "verdict_reasoning": r.get("verdict_reasoning"),
        "ai_provider": result.provider,
        "tokens_used": result.prompt_tokens + result.completion_tokens,
    }


@router.get("/stats")
async def get_strategy_stats(seller_id: int, db: AsyncSession = Depends(get_db)):
    """
    Strateji başarı panosu: operasyon tipine göre istatistikler.
    Yeni strateji başlatılırken AI'a context olarak beslenir.
    """
    # Tamamlanan stratejiler
    outcomes_q = await db.execute(
        select(StrategyOutcome, Strategy)
        .join(Strategy, StrategyOutcome.strategy_id == Strategy.id)
        .where(Strategy.seller_id == seller_id)
    )
    rows = outcomes_q.all()

    if not rows:
        return {
            "total_completed": 0,
            "overall_success_rate": 0,
            "by_operation_type": {},
            "avg_timeline_days": 0,
            "most_successful_operation": None,
            "ai_context_summary": "Henüz tamamlanmış strateji yok.",
        }

    by_op: dict[str, dict] = {}
    total_days = 0

    for outcome, strategy in rows:
        op = strategy.operation_type
        if op not in by_op:
            by_op[op] = {"total": 0, "success": 0, "partial": 0, "failed": 0, "total_days": 0}

        by_op[op]["total"] += 1
        by_op[op][outcome.outcome] = by_op[op].get(outcome.outcome, 0) + 1

        days = (outcome.completed_at - strategy.initiated_at).days
        by_op[op]["total_days"] += days
        total_days += days

    # Başarı oranları
    result_by_op = {}
    for op, data in by_op.items():
        success_rate = round((data["success"] + data["partial"] * 0.5) / data["total"] * 100, 1)
        result_by_op[op] = {
            "total": data["total"],
            "success": data.get("success", 0),
            "partial": data.get("partial", 0),
            "failed": data.get("failed", 0),
            "success_rate_pct": success_rate,
            "avg_days": round(data["total_days"] / data["total"], 1),
        }

    total = len(rows)
    overall_success = sum(
        (d["success"] + d["partial"] * 0.5) for d in result_by_op.values()
    ) / total * 100

    best_op = max(result_by_op.items(), key=lambda x: x[1]["success_rate_pct"])[0]

    # AI için bağlam özeti
    ai_summary = (
        f"{total} tamamlanmış strateji. Genel başarı oranı: %{overall_success:.0f}. "
        f"En başarılı operasyon: '{best_op}'. "
        + " | ".join(
            f"{op}: %{d['success_rate_pct']} başarı ({d['total']} strateji)"
            for op, d in result_by_op.items()
        )
    )

    return {
        "total_completed": total,
        "overall_success_rate": round(overall_success, 1),
        "by_operation_type": result_by_op,
        "avg_timeline_days": round(total_days / total, 1) if total else 0,
        "most_successful_operation": best_op,
        "ai_context_summary": ai_summary,
    }


@router.get("/{strategy_id}/projection")
async def get_strategy_projection(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """
    Erken uyarı: mevcut hızla hedefe ulaşılır mı?
    Checkpoint verisiyle lineer ekstrapolasyon.
    """
    s = await db.get(Strategy, strategy_id)
    if not s:
        raise HTTPException(404, "Strategy not found")

    cp_result = await db.execute(
        select(StrategyCheckpoint)
        .where(StrategyCheckpoint.strategy_id == strategy_id)
        .order_by(StrategyCheckpoint.checked_at)
    )
    checkpoints = cp_result.scalars().all()

    timeline_days = (s.target_date - s.initiated_at).days
    days_elapsed = (datetime.utcnow() - s.initiated_at).days

    checkpoint_data = [
        {
            "day": (cp.checked_at - s.initiated_at).days,
            "progress_pct": cp.progress_pct or 0,
        }
        for cp in checkpoints
    ]

    proj = project_strategy_outcome(
        checkpoints=checkpoint_data,
        target_date_days=timeline_days,
        days_elapsed=days_elapsed,
    )

    return {
        "strategy_id": strategy_id,
        "current_progress_pct": proj.current_progress_pct,
        "projected_completion_day": proj.projected_completion_day,
        "will_meet_deadline": proj.will_meet_deadline,
        "days_remaining": proj.days_remaining,
        "velocity_per_day": proj.velocity,
        "warning": proj.warning,
        "confidence": proj.confidence,
        "timeline_days": timeline_days,
        "days_elapsed": days_elapsed,
    }


@router.get("/{strategy_id}/context")
async def get_strategy_context_for_next_ai(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """
    Bir önceki tamamlanmış strateji context'ini döndürür.
    Yeni strateji başlatılırken AI'a bu veri beslenir.
    """
    outcome = await db.execute(
        select(StrategyOutcome).where(StrategyOutcome.strategy_id == strategy_id)
    )
    outcome = outcome.scalar_one_or_none()
    if not outcome:
        raise HTTPException(status_code=404, detail="No outcome yet")

    return {
        "previous_outcome": outcome.outcome,
        "lessons_learned": outcome.lessons_learned,
        "next_strategy_hints": outcome.next_strategy_hints,
        "context_for_next_ai": outcome.next_strategy_hints.get("context_for_next_ai") if outcome.next_strategy_hints else None,
    }
