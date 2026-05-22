"""
Temel analitik algoritmalar:
- Gerçek kârlılık hesabı (ROAS, TACoS, Net Profit, Break-even ACOS)
- EMA trend analizi (7/30 gün)
- Z-Score anomali tespiti
- Ad Worthiness Score
- Bütçe optimizasyonu (gradient descent)
- Attribution modeli
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Literal


# ─── Kârlılık Hesabı ────────────────────────────────────────────────────────

@dataclass
class ProfitabilityResult:
    roas: float
    acos: float                  # %
    tacos: float                 # %
    break_even_acos: float       # % — bu değerin altında reklam karlı
    net_profit_per_sale: float
    is_profitable: bool
    profit_margin: float         # %
    recommendation: Literal["increase_budget", "maintain", "reduce_budget", "pause_ads"]
    budget_change_pct: int       # +20 → %20 artır, -30 → %30 azalt


def calculate_profitability(
    revenue: float,
    ad_spend: float,
    total_revenue: float,
    cogs: float,
    shipping_cost: float,
    etsy_fee_pct: float = 0.065,
    etsy_listing_fee: float = 0.20,
    price: float | None = None,
) -> ProfitabilityResult:
    """
    Bir ürün için gerçek kârlılık hesabı.
    revenue: Reklamdan gelen gelir
    total_revenue: Organik + reklam toplam gelir
    """
    price_used = price or (revenue / max(1, round(revenue / max(cogs, 1))))
    etsy_fees = revenue * etsy_fee_pct + etsy_listing_fee
    net_profit = revenue - cogs - shipping_cost - etsy_fees - ad_spend
    profit_margin = (revenue - cogs - shipping_cost - etsy_fees) / max(revenue, 0.01)
    break_even_acos = profit_margin * 100

    roas = revenue / ad_spend if ad_spend > 0 else 0.0
    acos = (ad_spend / revenue * 100) if revenue > 0 else 0.0
    tacos = (ad_spend / total_revenue * 100) if total_revenue > 0 else 0.0

    is_profitable = acos < break_even_acos

    if roas >= 3.5:
        recommendation = "increase_budget"
        budget_change_pct = 20
    elif roas >= 2.0:
        recommendation = "maintain"
        budget_change_pct = 0
    elif roas >= 1.0:
        recommendation = "reduce_budget"
        budget_change_pct = -30
    else:
        recommendation = "pause_ads"
        budget_change_pct = -100

    return ProfitabilityResult(
        roas=round(roas, 2),
        acos=round(acos, 2),
        tacos=round(tacos, 2),
        break_even_acos=round(break_even_acos, 2),
        net_profit_per_sale=round(net_profit, 2),
        is_profitable=is_profitable,
        profit_margin=round(profit_margin * 100, 2),
        recommendation=recommendation,
        budget_change_pct=budget_change_pct,
    )


# ─── EMA Trend Analizi ───────────────────────────────────────────────────────

def calculate_ema(values: list[float], period: int) -> list[float]:
    """Exponential Moving Average. values = [oldest, ..., newest]"""
    if not values:
        return []
    k = 2 / (period + 1)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return [round(e, 4) for e in ema]


@dataclass
class TrendResult:
    ema_7d: float
    ema_30d: float
    trend: Literal["improving", "stable", "declining"]
    change_pct: float  # 7d EMA'nın 30d EMA'ya göre % farkı


def analyze_trend(daily_values: list[float]) -> TrendResult:
    """
    Son 30+ günlük veri listesi alır, 7d ve 30d EMA üretir ve trendi yorumlar.
    daily_values = [oldest, ..., newest]
    """
    if len(daily_values) < 7:
        last = daily_values[-1] if daily_values else 0.0
        return TrendResult(ema_7d=last, ema_30d=last, trend="stable", change_pct=0.0)

    ema7 = calculate_ema(daily_values[-7:], 7)[-1]
    ema30 = calculate_ema(daily_values, min(30, len(daily_values)))[-1]

    change_pct = ((ema7 - ema30) / ema30 * 100) if ema30 != 0 else 0.0

    if change_pct > 5:
        trend = "improving"
    elif change_pct < -5:
        trend = "declining"
    else:
        trend = "stable"

    return TrendResult(
        ema_7d=round(ema7, 4),
        ema_30d=round(ema30, 4),
        trend=trend,
        change_pct=round(change_pct, 2),
    )


# ─── Z-Score Anomali Tespiti ─────────────────────────────────────────────────

@dataclass
class AnomalyResult:
    metric_name: str
    current_value: float
    expected_value: float
    z_score: float
    is_anomaly: bool
    severity: Literal["normal", "warning", "critical"]
    direction: Literal["spike", "drop", "normal"]
    message: str


def detect_anomaly(
    metric_name: str,
    current_value: float,
    historical_values: list[float],
    warning_threshold: float = 2.0,
    critical_threshold: float = 3.0,
) -> AnomalyResult:
    """
    Rolling Z-score ile anomali tespiti.
    historical_values: Son N günlük değerler (mevcut gün hariç).
    """
    if len(historical_values) < 5:
        return AnomalyResult(
            metric_name=metric_name, current_value=current_value,
            expected_value=current_value, z_score=0.0,
            is_anomaly=False, severity="normal", direction="normal",
            message="Yeterli geçmiş veri yok.",
        )

    n = len(historical_values)
    mean = sum(historical_values) / n
    variance = sum((x - mean) ** 2 for x in historical_values) / n
    std = math.sqrt(variance) if variance > 0 else 0.0001

    z = (current_value - mean) / std
    abs_z = abs(z)

    if abs_z >= critical_threshold:
        severity = "critical"
        is_anomaly = True
    elif abs_z >= warning_threshold:
        severity = "warning"
        is_anomaly = True
    else:
        severity = "normal"
        is_anomaly = False

    direction = "spike" if z > 0 else ("drop" if z < 0 else "normal")

    metric_labels = {
        "roas": "ROAS", "acos": "ACOS", "ctr": "CTR",
        "conversion_rate": "Dönüşüm Oranı", "ad_spend": "Reklam Harcaması",
    }
    label = metric_labels.get(metric_name, metric_name.upper())

    if is_anomaly:
        direction_tr = "ani artış" if direction == "spike" else "ani düşüş"
        message = (
            f"{label} değeri {direction_tr} gösterdi. "
            f"Mevcut: {current_value:.2f}, Beklenen: {mean:.2f} (±{std:.2f}), "
            f"Z-Score: {z:.2f}"
        )
    else:
        message = f"{label} normal aralıkta. Z-Score: {z:.2f}"

    return AnomalyResult(
        metric_name=metric_name,
        current_value=round(current_value, 4),
        expected_value=round(mean, 4),
        z_score=round(z, 3),
        is_anomaly=is_anomaly,
        severity=severity,
        direction=direction,
        message=message,
    )


# ─── Ad Worthiness Score ─────────────────────────────────────────────────────

@dataclass
class AdWorthinessResult:
    score: int                   # 0-100
    recommendation: Literal["dont_advertise", "test_small_budget", "recommend", "priority"]
    view_situation: str
    view_diagnosis: str
    pre_ad_action: str | None    # Reklam öncesi yapılması gereken, varsa
    reasons: list[str]
    suggested_daily_budget: float


def calculate_ad_worthiness(
    views_30d: int,
    sales_30d: int,
    profit_margin: float,         # 0.0 - 1.0
    inventory: int,
    roas_trend: Literal["improving", "stable", "declining"],
    seasonal_demand_score: float = 0.5,  # 0.0 - 1.0
    current_daily_budget: float = 0.0,
) -> AdWorthinessResult:
    """
    Ürün için reklam uygunluk skoru hesaplar (0-100).
    """
    score = 0
    reasons: list[str] = []
    pre_ad_action: str | None = None

    conversion_rate = sales_30d / max(views_30d, 1)

    # Görünürlük + dönüşüm analizi
    if views_30d > 200 and conversion_rate < 0.02:
        situation = "high_views_low_sales"
        diagnosis = "Çok görüntülenme var ama satış az. Listing sorunu olabilir (fiyat, fotoğraf, başlık)."
        pre_ad_action = "Listing'i düzelt (fotoğraf, fiyat, başlık) — reklam öncesi conversion_rate'i artır."
        score += 20  # Trafik var, potansiyel de var
    elif views_30d < 50 and conversion_rate >= 0.05:
        situation = "low_views_good_conversion"
        diagnosis = "Az görüntülenme ama iyi dönüşüm. Reklam ile trafik artırılabilir."
        score += 35
        reasons.append("Dönüşüm oranı güçlü — reklam trafiği karlıya çevirir.")
    elif views_30d < 50 and conversion_rate < 0.02:
        situation = "low_views_low_conversion"
        diagnosis = "Hem görünürlük hem dönüşüm düşük. Listing ve reklam birlikte iyileştirilmeli."
        pre_ad_action = "Önce listing kalitesini artır, sonra küçük bütçeyle test et."
        score += 10
    else:
        situation = "balanced"
        diagnosis = "Görünürlük ve dönüşüm dengeli."
        score += 25

    # Kâr marjı yeterliliği
    if profit_margin >= 0.40:
        score += 25
        reasons.append(f"Yüksek kâr marjı ({profit_margin*100:.0f}%) — reklam maliyetini karşılar.")
    elif profit_margin >= 0.25:
        score += 15
        reasons.append(f"Yeterli kâr marjı ({profit_margin*100:.0f}%).")
    else:
        reasons.append(f"Düşük kâr marjı ({profit_margin*100:.0f}%) — reklam riskli.")

    # Trend
    if roas_trend == "improving":
        score += 20
        reasons.append("ROAS trendi yukarı — momentum var.")
    elif roas_trend == "stable":
        score += 10
    else:
        reasons.append("ROAS trendi aşağı — dikkatli ol.")

    # Envanter
    if inventory >= 20:
        score += 10
        reasons.append("Yeterli stok var.")
    elif inventory >= 5:
        score += 5
    else:
        reasons.append("Düşük stok — reklam başlamadan önce stok tamamla.")

    # Mevsimsel uyum
    if seasonal_demand_score >= 0.7:
        score += 10
        reasons.append("Mevsimsel talep yüksek.")
    elif seasonal_demand_score >= 0.4:
        score += 5

    score = min(score, 100)

    if score >= 80:
        recommendation = "priority"
    elif score >= 60:
        recommendation = "recommend"
    elif score >= 30:
        recommendation = "test_small_budget"
    else:
        recommendation = "dont_advertise"

    # Önerilen günlük bütçe
    if recommendation == "priority":
        suggested_budget = max(current_daily_budget * 1.2, 15.0)
    elif recommendation == "recommend":
        suggested_budget = max(current_daily_budget or 5.0, 5.0)
    elif recommendation == "test_small_budget":
        suggested_budget = 3.0
    else:
        suggested_budget = 0.0

    return AdWorthinessResult(
        score=score,
        recommendation=recommendation,
        view_situation=situation,
        view_diagnosis=diagnosis,
        pre_ad_action=pre_ad_action,
        reasons=reasons,
        suggested_daily_budget=round(suggested_budget, 2),
    )


# ─── Bütçe Optimizasyonu (Gradient Descent) ──────────────────────────────────

@dataclass
class BudgetAllocation:
    product_id: int
    product_title: str
    current_budget: float
    suggested_budget: float
    roas: float
    reason: str


def optimize_budget(
    products: list[dict],
    total_budget: float,
    learning_rate: float = 0.05,
) -> list[BudgetAllocation]:
    """
    ROAS'a göre gradient descent ile bütçe optimizasyonu.
    products: [{"id": 1, "title": "...", "roas": 3.5, "current_budget": 5.0}, ...]
    """
    if not products or total_budget <= 0:
        return []

    eligible = [p for p in products if p.get("roas", 0) > 0]
    if not eligible:
        return []

    # Gradient: ROAS'a göre ağırlık hesapla
    roas_sum = sum(p["roas"] for p in eligible)
    step = learning_rate * total_budget / len(eligible)

    allocations: list[BudgetAllocation] = []
    remaining = total_budget

    for p in sorted(eligible, key=lambda x: x["roas"], reverse=True):
        roas = p["roas"]
        weight = roas / roas_sum
        raw_budget = total_budget * weight

        if roas >= 3.5:
            final_budget = min(raw_budget + step, remaining * 0.4)
            reason = f"ROAS {roas:.1f} — bütçe öncelikli"
        elif roas >= 2.0:
            final_budget = raw_budget
            reason = f"ROAS {roas:.1f} — bütçe korunuyor"
        elif roas >= 1.0:
            final_budget = raw_budget - step
            reason = f"ROAS {roas:.1f} — bütçe azaltılıyor"
        else:
            final_budget = 0.0
            reason = f"ROAS {roas:.1f} < 1.0 — reklam durdur"

        final_budget = max(0.0, round(final_budget, 2))
        remaining -= final_budget

        allocations.append(BudgetAllocation(
            product_id=p["id"],
            product_title=p.get("title", ""),
            current_budget=p.get("current_budget", 0.0),
            suggested_budget=final_budget,
            roas=roas,
            reason=reason,
        ))

    return allocations


# ─── Attribution Modeli ───────────────────────────────────────────────────────

@dataclass
class TouchPoint:
    ad_id: str
    timestamp: float  # Unix timestamp
    revenue: float


def attribute_revenue(
    touchpoints: list[TouchPoint],
    model: Literal["first_touch", "last_touch", "linear", "time_decay"] = "linear",
) -> dict[str, float]:
    """
    Geliri temas noktalarına dağıt.
    Döndürür: {ad_id: attributed_revenue}
    """
    if not touchpoints:
        return {}

    total_revenue = touchpoints[-1].revenue  # Son temas noktasındaki dönüşüm geliri
    n = len(touchpoints)

    if model == "first_touch":
        return {touchpoints[0].ad_id: total_revenue}

    if model == "last_touch":
        return {touchpoints[-1].ad_id: total_revenue}

    if model == "linear":
        per_touch = total_revenue / n
        result: dict[str, float] = {}
        for tp in touchpoints:
            result[tp.ad_id] = result.get(tp.ad_id, 0.0) + per_touch
        return result

    if model == "time_decay":
        # Sonraki temas daha değerli: üssel ağırlık
        t_max = touchpoints[-1].timestamp
        weights = [math.exp((tp.timestamp - t_max) / 86400) for tp in touchpoints]  # 1 gün decay
        w_sum = sum(weights)
        result = {}
        for tp, w in zip(touchpoints, weights):
            result[tp.ad_id] = result.get(tp.ad_id, 0.0) + (w / w_sum) * total_revenue
        return result

    return {}
