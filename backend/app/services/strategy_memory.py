"""
StrategyMemory — AI Öğrenme Döngüsü

Bu servis iki şeyi çözer:

1. BAĞLAM ZENGİNLEŞTİRME
   Tamamlanan stratejilerden pattern çıkarır ve her yeni AI çağrısına
   "bu satıcıya daha önce ne önerdik, ne işe yaradı" bilgisini ekler.
   Claude artık 4 sayı değil, gerçek geçmiş görür.

2. ETKİ ÖLÇÜMÜ
   Her verdict sonrasında AI'ın güven skoru ile gerçek sonucu karşılaştırır.
   "Claude yüksek güven dediğinde %X isabet ediyor" sorusunu yanıtlar.
   Bu veri sıradaki öneri kararını güçlendirir.

Kullanım:
    memory = await StrategyMemory.build(seller_id=1, db=db)
    context_block = memory.to_prompt_block()       # AI prompt'una eklenir
    impact = memory.calculate_impact(strategy, outcome)  # verdict'te çağrılır
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.strategy import Strategy, StrategyOutcome


# ─── Veri Yapıları ──────────────────────────────────────────────────────────

@dataclass
class OperationPattern:
    """Bir operasyon tipinin tarihsel başarı özeti."""
    operation_type: str
    total: int
    success: int
    partial: int
    failed: int
    avg_roas_change_pct: float   # Başarılı stratejilerde ortalama ROAS artışı
    avg_duration_days: float
    best_outcome_summary: str    # En iyi sonuçtan alınan öğrenme notu
    last_used: str | None        # ISO8601 tarih

    @property
    def success_rate(self) -> float:
        return self.success / self.total if self.total > 0 else 0.0

    @property
    def label(self) -> str:
        labels = {
            "increase_budget": "Bütçe Artışı",
            "reduce_budget": "Bütçe Düşürme",
            "test_budget": "Bütçe Testi",
            "optimize_listing": "Listing Optimizasyonu",
            "pause_ads": "Reklam Durdurma",
        }
        return labels.get(self.operation_type, self.operation_type)


@dataclass
class SellerBehaviorProfile:
    """Satıcının aksiyona geçme ve tutarlılık örüntüleri."""
    avg_days_to_action: float      # Öneri→uygulama arası ortalama gün
    follows_through_rate: float    # Başlattığı stratejileri bitirme oranı
    preferred_operation: str | None  # En çok başvurduğu operasyon tipi
    risk_tolerance: Literal["conservative", "moderate", "aggressive"]
    total_strategies_run: int
    active_since_days: int


@dataclass
class ImpactScore:
    """
    Tek bir stratejinin etki skoru.

    Hesaplama:
    - outcome_quality: success=1.0, partial=0.5, failed=0.0
    - confidence_match: AI yüksek güven tahmin ettiyse ve yanılıyorsa ceza
    - impact_score = outcome_quality × confidence_match
    """
    strategy_id: int
    outcome: str
    ai_confidence: str          # low | medium | high
    outcome_quality: float      # 0-1
    confidence_match: float     # 0-1 (AI ne kadar isabetliydi)
    impact_score: float         # 0-1 (genel etki
    actual_roas_change_pct: float
    predicted_roas_change_pct: float
    verdict: str                # "AI isabetli", "AI aşırı iyimser", "AI aşırı kötümser"


@dataclass
class SellerMemory:
    """
    Bir satıcı için tam AI bağlam bloğu.
    Bu nesne her AI çağrısının prompt'una eklenir.
    """
    seller_id: int
    patterns: list[OperationPattern]
    behavior: SellerBehaviorProfile
    recent_context_chain: list[str]   # Son 3 verdict'ten context_for_next_ai
    calibration: dict                 # AI isabet oranı kalibrasyonu
    built_at: str

    def to_prompt_block(self) -> str:
        """
        Prompt'a eklenecek bağlam metni.
        Kısa ve bilgi yoğun — Claude'un alabileceği en değerli input.
        """
        lines: list[str] = ["<seller_memory>"]

        # Operasyon pattern'leri
        if self.patterns:
            lines.append("Geçmiş strateji başarı oranları:")
            for p in self.patterns:
                sr = f"%{p.success_rate * 100:.0f}"
                roas_note = f", ortalama ROAS +%{p.avg_roas_change_pct:.0f}" if p.avg_roas_change_pct > 0 else ""
                lines.append(
                    f"  - {p.label}: {p.total} deneme, {sr} başarılı{roas_note}"
                )
                if p.best_outcome_summary:
                    lines.append(f"    En iyi öğrenme: {p.best_outcome_summary}")

        # Satıcı davranışı
        b = self.behavior
        if b.total_strategies_run > 0:
            lines.append(
                f"Satıcı profili: {b.total_strategies_run} strateji denendi, "
                f"tamamlama oranı %{b.follows_through_rate * 100:.0f}, "
                f"risk toleransı: {b.risk_tolerance}"
            )
            if b.preferred_operation:
                lines.append(f"  Tercih ettiği yöntem: {b.preferred_operation}")

        # Önceki verdict'lerden taşınan bağlam
        if self.recent_context_chain:
            lines.append("Önceki stratejilerden taşınan kritik bilgi:")
            for ctx in self.recent_context_chain[-3:]:
                lines.append(f"  → {ctx}")

        # AI kalibrasyon bilgisi
        cal = self.calibration
        if cal.get("total_scored", 0) >= 3:
            lines.append(
                f"AI kalibrasyon (bu satıcı için): "
                f"{cal['total_scored']} öneride %{cal['accuracy_pct']:.0f} isabet. "
                f"Yüksek güven tahminleri %{cal['high_confidence_accuracy_pct']:.0f} isabetli."
            )

        lines.append("</seller_memory>")
        return "\n".join(lines)

    def is_empty(self) -> bool:
        return self.behavior.total_strategies_run == 0


# ─── StrategyMemory Builder ──────────────────────────────────────────────────

class StrategyMemory:
    """
    DB'den satıcının tüm strateji geçmişini okur ve SellerMemory oluşturur.
    Her AI çağrısında `await StrategyMemory.build(seller_id, db)` ile çağrılır.
    """

    @staticmethod
    async def build(seller_id: int, db: AsyncSession) -> SellerMemory:
        """Seller'ın tüm strateji geçmişini okuyup bağlam oluşturur."""

        # Tüm stratejileri çek
        q = await db.execute(
            select(Strategy)
            .where(Strategy.seller_id == seller_id)
            .order_by(Strategy.initiated_at.desc())
        )
        strategies = q.scalars().all()

        # Outcome'ları çek
        completed_ids = [s.id for s in strategies if s.status in ("completed", "failed")]
        outcomes: dict[int, StrategyOutcome] = {}
        if completed_ids:
            oq = await db.execute(
                select(StrategyOutcome).where(StrategyOutcome.strategy_id.in_(completed_ids))
            )
            for o in oq.scalars().all():
                outcomes[o.strategy_id] = o

        # ── Operasyon Pattern'leri ────────────────────────────────────────
        op_data: dict[str, dict] = {}
        for s in strategies:
            op = s.operation_type
            if op not in op_data:
                op_data[op] = {
                    "total": 0, "success": 0, "partial": 0, "failed": 0,
                    "roas_changes": [], "durations": [],
                    "best_lesson": "", "last_used": None,
                }
            d = op_data[op]
            d["total"] += 1
            d["last_used"] = s.initiated_at.isoformat() if s.initiated_at else None

            o = outcomes.get(s.id)
            if o:
                result = o.outcome
                d[result] = d.get(result, 0) + 1

                # ROAS değişimi
                if o.final_metrics and s.initial_metrics:
                    roas_start = (s.initial_metrics or {}).get("roas", 0)
                    roas_end = (o.final_metrics or {}).get("roas", roas_start)
                    if roas_start > 0:
                        change_pct = ((roas_end - roas_start) / roas_start) * 100
                        d["roas_changes"].append(change_pct)

                # Süre
                if s.initiated_at and o.completed_at:
                    dur = (o.completed_at - s.initiated_at).days
                    d["durations"].append(dur)

                # En iyi öğrenme notu
                if result == "success" and not d["best_lesson"]:
                    lessons = (o.lessons_learned or [])
                    if lessons:
                        d["best_lesson"] = lessons[0][:120]

        patterns = []
        for op, d in op_data.items():
            avg_roas = (
                sum(d["roas_changes"]) / len(d["roas_changes"])
                if d["roas_changes"] else 0.0
            )
            avg_dur = (
                sum(d["durations"]) / len(d["durations"])
                if d["durations"] else 0.0
            )
            patterns.append(OperationPattern(
                operation_type=op,
                total=d["total"],
                success=d.get("success", 0),
                partial=d.get("partial", 0),
                failed=d.get("failed", 0),
                avg_roas_change_pct=round(avg_roas, 1),
                avg_duration_days=round(avg_dur, 1),
                best_outcome_summary=d["best_lesson"],
                last_used=d["last_used"],
            ))
        patterns.sort(key=lambda p: p.total, reverse=True)

        # ── Satıcı Davranış Profili ───────────────────────────────────────
        total = len(strategies)
        completed_count = len(outcomes)
        follow_through = completed_count / total if total > 0 else 0.0

        preferred = None
        if op_data:
            preferred = max(op_data, key=lambda op: op_data[op]["total"])

        # Risk toleransı: increase_budget ağırlıklı → aggressive, pause/reduce → conservative
        aggressive_ops = sum(
            op_data.get(op, {}).get("total", 0)
            for op in ("increase_budget", "test_budget")
        )
        conservative_ops = sum(
            op_data.get(op, {}).get("total", 0)
            for op in ("reduce_budget", "pause_ads")
        )
        if aggressive_ops > conservative_ops * 2:
            risk: Literal["conservative", "moderate", "aggressive"] = "aggressive"
        elif conservative_ops > aggressive_ops * 2:
            risk = "conservative"
        else:
            risk = "moderate"

        # Kaç gündür aktif
        oldest = min((s.initiated_at for s in strategies if s.initiated_at), default=None)
        active_since = (datetime.utcnow() - oldest).days if oldest else 0

        behavior = SellerBehaviorProfile(
            avg_days_to_action=0.0,  # TODO: öneri→aksiyon süresi ölçümü gelince doldur
            follows_through_rate=round(follow_through, 2),
            preferred_operation=preferred,
            risk_tolerance=risk,
            total_strategies_run=total,
            active_since_days=active_since,
        )

        # ── Context Chain (son verdict'lerden taşınan bilgi) ──────────────
        recent_context: list[str] = []
        for s in strategies[:10]:
            o = outcomes.get(s.id)
            if o and o.next_strategy_hints:
                ctx = o.next_strategy_hints.get("context_for_next_ai", "")
                if ctx and ctx not in recent_context:
                    recent_context.append(ctx)
            if len(recent_context) >= 3:
                break

        # ── AI Kalibrasyon ────────────────────────────────────────────────
        calibration = StrategyMemory._calculate_calibration(strategies, outcomes)

        return SellerMemory(
            seller_id=seller_id,
            patterns=patterns,
            behavior=behavior,
            recent_context_chain=recent_context,
            calibration=calibration,
            built_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _calculate_calibration(
        strategies: list,
        outcomes: dict[int, StrategyOutcome],
    ) -> dict:
        """
        AI'ın güven skoru ile gerçek sonucu karşılaştır.
        impact_score kolonu dolu olan stratejiler üzerinden hesaplar.
        """
        scored = [
            s for s in strategies
            if getattr(s, "ai_confidence_score", None) is not None
            and s.id in outcomes
        ]

        if len(scored) < 2:
            return {"total_scored": len(scored), "accuracy_pct": 0.0, "high_confidence_accuracy_pct": 0.0}

        correct = 0
        high_conf_total = 0
        high_conf_correct = 0

        for s in scored:
            o = outcomes[s.id]
            confidence = s.ai_confidence_score or 0.5
            outcome_ok = o.outcome in ("success", "partial")

            # Yüksek güven (>0.6) + başarılı sonuç → isabetli
            if outcome_ok:
                correct += 1
            if confidence > 0.6:
                high_conf_total += 1
                if outcome_ok:
                    high_conf_correct += 1

        accuracy = (correct / len(scored)) * 100
        hc_accuracy = (high_conf_correct / high_conf_total * 100) if high_conf_total > 0 else 0.0

        return {
            "total_scored": len(scored),
            "accuracy_pct": round(accuracy, 1),
            "high_confidence_accuracy_pct": round(hc_accuracy, 1),
        }

    @staticmethod
    def calculate_impact(
        strategy: Strategy,
        outcome: StrategyOutcome,
    ) -> ImpactScore:
        """
        Verdict anında çağrılır. AI güven skoru vs gerçek sonucu karşılaştırır.
        Sonuç Strategy.ai_confidence_score ve StrategyOutcome.impact_score'a yazılır.
        """
        # Gerçek sonuç kalitesi
        outcome_quality = {"success": 1.0, "partial": 0.5, "failed": 0.0}.get(
            outcome.outcome, 0.0
        )

        # AI güven skoru (launch_strategy'den gelen)
        launch_analysis = strategy.ai_launch_analysis or {}
        confidence_str = launch_analysis.get("confidence", "medium")
        confidence_score = {"low": 0.33, "medium": 0.66, "high": 1.0}.get(confidence_str, 0.5)

        # Güven isabeti: yüksek güven + başarı → 1.0, yüksek güven + başarısız → 0.0
        if confidence_score >= 0.66 and outcome_quality >= 0.5:
            confidence_match = 1.0  # İsabetli yüksek güven
        elif confidence_score >= 0.66 and outcome_quality < 0.5:
            confidence_match = 0.1  # Yüksek güven ama yanılmış — ceza
        elif confidence_score < 0.66 and outcome_quality >= 0.5:
            confidence_match = 0.8  # Düşük güven ama başardı — hafif bonus
        else:
            confidence_match = 0.6  # Düşük güven + başarısız — nötr

        impact = round(outcome_quality * confidence_match, 3)

        # ROAS değişimi
        roas_start = (strategy.initial_metrics or {}).get("roas", 0)
        roas_end = (outcome.final_metrics or {}).get("roas", roas_start)
        actual_change = ((roas_end - roas_start) / roas_start * 100) if roas_start > 0 else 0.0

        target = (strategy.target_metrics or {}).get("roas", roas_start)
        predicted_change = ((target - roas_start) / roas_start * 100) if roas_start > 0 else 0.0

        # Sözel verdict
        if confidence_score >= 0.66 and outcome_quality >= 0.5:
            verdict = "AI isabetli — yüksek güven doğrulandı"
        elif confidence_score >= 0.66 and outcome_quality < 0.5:
            verdict = "AI aşırı iyimser — yüksek güven yanılttı"
        elif confidence_score < 0.66 and outcome_quality >= 0.5:
            verdict = "AI ihtiyatlıydı — sonuç beklentinin üstünde"
        else:
            verdict = "AI ihtiyatlıydı — sonuç beklenti dahilinde"

        return ImpactScore(
            strategy_id=strategy.id,
            outcome=outcome.outcome,
            ai_confidence=confidence_str,
            outcome_quality=outcome_quality,
            confidence_match=confidence_match,
            impact_score=impact,
            actual_roas_change_pct=round(actual_change, 1),
            predicted_roas_change_pct=round(predicted_change, 1),
            verdict=verdict,
        )
