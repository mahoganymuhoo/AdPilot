"""
Temel analitik algoritmalar:
- Gerçek kârlılık hesabı (ROAS, TACoS, Net Profit, Break-even ACOS)
- EMA trend analizi (7/30 gün)
- Z-Score anomali tespiti
- Ad Worthiness Score
- Bütçe optimizasyonu (gradient descent)
- Budget Saturation Curve (logaritmik fit)
- Break-even Stress Test (senaryo matrisi)
- Listing Kalite Skoru (CTR / kategori benchmark)
- Ürün Yaşam Döngüsü (launch/growth/mature/declining)
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


# ─── Budget Saturation Curve ─────────────────────────────────────────────────

@dataclass
class SaturationCurveResult:
    curve_points: list[dict]       # [{"budget": x, "projected_roas": y}, ...]
    optimal_budget: float          # En yüksek verim noktası
    current_efficiency_pct: float  # Mevcut bütçenin optimal'e % ne kadar yakın
    diminishing_return_budget: float  # Verimin belirgin azaldığı nokta
    recommendation: str


def calculate_saturation_curve(
    budget_roas_history: list[dict],  # [{"budget": 5.0, "roas": 4.2}, ...]
    current_budget: float,
    max_budget: float | None = None,
) -> SaturationCurveResult:
    """
    Geçmiş (bütçe, ROAS) çiftlerine logaritmik fit uygular.
    ROAS = a * ln(budget) + b
    Veri yoksa veya az varsa sabit çarpan ile tahmin üretir.
    """
    if max_budget is None:
        max_budget = current_budget * 5

    # Logaritmik fit: en az 3 nokta gerekli
    if len(budget_roas_history) >= 3:
        budgets = [p["budget"] for p in budget_roas_history if p["budget"] > 0]
        roas_vals = [p["roas"] for p in budget_roas_history if p["budget"] > 0]

        # Manuel least squares: a, b için
        ln_b = [math.log(b) for b in budgets]
        n = len(budgets)
        sum_x = sum(ln_b)
        sum_y = sum(roas_vals)
        sum_xy = sum(x * y for x, y in zip(ln_b, roas_vals))
        sum_x2 = sum(x * x for x in ln_b)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-9:
            a, b = 0.5, sum_y / n
        else:
            a = (n * sum_xy - sum_x * sum_y) / denom
            b = (sum_y - a * sum_x) / n
    else:
        # Yeterli veri yok — tipik e-ticaret eğrisi kullan
        if budget_roas_history:
            ref = budget_roas_history[0]
            ref_budget = max(ref["budget"], 1)
            ref_roas = ref["roas"]
        else:
            ref_budget = current_budget
            ref_roas = 3.0
        a = ref_roas / (2 * math.log(max(ref_budget, 1) + 1))
        b = ref_roas - a * math.log(max(ref_budget, 1))

    # Eğri noktaları üret (20 nokta)
    step = max_budget / 20
    curve_points = []
    for i in range(1, 22):
        bgt = round(step * i, 2)
        projected_roas = max(0.1, a * math.log(max(bgt, 0.01)) + b)
        curve_points.append({"budget": bgt, "projected_roas": round(projected_roas, 3)})

    # Optimal bütçe: marjinal ROAS artışının en yüksek olduğu nokta (türev max)
    # d(ROAS)/d(budget) = a / budget → maksimum düşük bütçede, "optimal" eşiği belirle
    # Pratik: ROAS'ın %80'ine ulaşılan minimum bütçe = optimal
    max_roas = max(p["projected_roas"] for p in curve_points)
    target_roas_threshold = max_roas * 0.80

    optimal_budget = curve_points[0]["budget"]
    for p in curve_points:
        if p["projected_roas"] >= target_roas_threshold:
            optimal_budget = p["budget"]
            break

    # Azalan verim noktası: ROAS artışının %10'un altına düştüğü yer
    diminishing_budget = max_budget
    for i in range(1, len(curve_points)):
        prev = curve_points[i - 1]["projected_roas"]
        curr = curve_points[i]["projected_roas"]
        gain_pct = (curr - prev) / max(prev, 0.01) * 100
        if gain_pct < 3:  # %3'ten az artış
            diminishing_budget = curve_points[i]["budget"]
            break

    # Mevcut bütçe verimliliği
    current_projected = max(0.1, a * math.log(max(current_budget, 0.01)) + b)
    efficiency_pct = min(100.0, round((current_projected / max_roas) * 100, 1))

    if current_budget < optimal_budget * 0.7:
        recommendation = f"Bütçeni ${optimal_budget:.0f}/güne artır — ROAS %{80} verimine ulaşırsın."
    elif current_budget > diminishing_budget:
        recommendation = f"${diminishing_budget:.0f}/gün üzerinde ek harcama çok az ROAS kazanımı sağlıyor."
    else:
        recommendation = "Mevcut bütçen verimli aralıkta. Büyük değişiklik gerekmez."

    return SaturationCurveResult(
        curve_points=curve_points,
        optimal_budget=round(optimal_budget, 2),
        current_efficiency_pct=efficiency_pct,
        diminishing_return_budget=round(diminishing_budget, 2),
        recommendation=recommendation,
    )


# ─── Break-even Stress Test ───────────────────────────────────────────────────

@dataclass
class StressScenario:
    label: str
    cogs_change_pct: float
    new_cogs: float
    new_break_even_acos: float
    new_net_profit: float
    is_still_profitable: bool
    margin_change_pts: float   # Kâr marjı değişimi (puan)


@dataclass
class StressTestResult:
    base_break_even_acos: float
    base_net_profit: float
    scenarios: list[StressScenario]
    safe_up_to_cogs_increase: float  # % — karlılığın korunduğu max COGS artışı


def stress_test_breakeven(
    price: float,
    cogs: float,
    shipping_cost: float,
    current_acos: float,
    cogs_change_steps: list[float] | None = None,
) -> StressTestResult:
    """
    COGS artışı senaryolarında karlılık simülasyonu.
    Döndürür: Her senaryo için break-even ACOS ve net kâr.
    """
    ETSY_FEE_PCT = 0.065
    LISTING_FEE = 0.20

    if cogs_change_steps is None:
        cogs_change_steps = [-20, -10, 0, 10, 20, 30, 50]

    def calc(new_cogs: float) -> tuple[float, float, float]:
        fees = price * ETSY_FEE_PCT + LISTING_FEE
        net_profit = price - new_cogs - shipping_cost - fees
        margin = net_profit / price if price > 0 else 0
        be_acos = max(0.0, margin * 100)
        return be_acos, net_profit, margin * 100

    base_be, base_np, base_margin = calc(cogs)

    scenarios = []
    safe_up_to = 0.0

    for pct in cogs_change_steps:
        new_cogs = round(cogs * (1 + pct / 100), 2)
        be, np_, margin = calc(new_cogs)
        is_profitable = current_acos <= be

        if pct > 0 and is_profitable:
            safe_up_to = pct

        scenarios.append(StressScenario(
            label=f"COGS {'+' if pct >= 0 else ''}{pct}%",
            cogs_change_pct=pct,
            new_cogs=new_cogs,
            new_break_even_acos=round(be, 2),
            new_net_profit=round(np_, 2),
            is_still_profitable=is_profitable,
            margin_change_pts=round(margin - base_margin, 2),
        ))

    return StressTestResult(
        base_break_even_acos=round(base_be, 2),
        base_net_profit=round(base_np, 2),
        scenarios=scenarios,
        safe_up_to_cogs_increase=safe_up_to,
    )


# ─── Listing Kalite Skoru ────────────────────────────────────────────────────

# Etsy kategori bazında ortalama CTR benchmark'ları (tahmini, güncellenir)
CATEGORY_CTR_BENCHMARKS: dict[str, float] = {
    "jewelry": 0.022,
    "home_decor": 0.018,
    "clothing": 0.020,
    "art": 0.015,
    "craft_supplies": 0.014,
    "toys": 0.019,
    "wedding": 0.025,
    "baby": 0.021,
    "default": 0.018,  # Kategori bilinmiyorsa
}


@dataclass
class ListingQualityResult:
    score: int                    # 0-100
    grade: Literal["poor", "average", "good", "excellent"]
    ctr_ratio: float              # Ürün CTR / Kategori ortalama
    product_ctr: float
    category_avg_ctr: float
    category: str
    recommendation: str
    issues: list[str]
    strengths: list[str]


def calculate_listing_quality(
    product_ctr: float,           # Ondalık (0.018 = %1.8)
    category: str = "default",
    title_word_count: int | None = None,
    has_video: bool = False,
    image_count: int = 1,
    review_count: int = 0,
    avg_rating: float = 0.0,
) -> ListingQualityResult:
    """
    Listing kalitesini CTR / kategori benchmark oranı üzerinden hesaplar.
    Ek sinyal: görsel sayısı, video, başlık uzunluğu, değerlendirme.
    """
    bench = CATEGORY_CTR_BENCHMARKS.get(category, CATEGORY_CTR_BENCHMARKS["default"])
    ctr_ratio = product_ctr / bench if bench > 0 else 1.0

    score = 0
    issues: list[str] = []
    strengths: list[str] = []

    # CTR oranı (maks 50 puan)
    if ctr_ratio >= 1.5:
        score += 50
        strengths.append(f"CTR kategori ortalamasının {ctr_ratio:.1f}x üzerinde.")
    elif ctr_ratio >= 1.1:
        score += 38
        strengths.append("CTR kategori ortalamasının üzerinde.")
    elif ctr_ratio >= 0.8:
        score += 25
    elif ctr_ratio >= 0.5:
        score += 12
        issues.append("CTR kategori ortalamasının oldukça altında — ana fotoğrafı güncelle.")
    else:
        score += 0
        issues.append("CTR çok düşük. Fotoğraf, başlık veya fiyat ciddi şekilde revize edilmeli.")

    # Görsel sayısı (maks 20 puan)
    if image_count >= 8:
        score += 20
        strengths.append("Yeterli görsel sayısı (8+).")
    elif image_count >= 5:
        score += 14
    elif image_count >= 3:
        score += 8
        issues.append("Görsel sayısını 5+ çıkarmak tıklama oranını artırır.")
    else:
        score += 0
        issues.append("Görsel sayısı çok az (1-2). En az 5 fotoğraf ekle.")

    # Video (10 puan)
    if has_video:
        score += 10
        strengths.append("Video var — listing dönüşüm oranını artırır.")
    else:
        issues.append("Video yok. Ürün videosu CTR'ı %15-25 artırabilir.")

    # Başlık uzunluğu (10 puan)
    if title_word_count is not None:
        if 8 <= title_word_count <= 15:
            score += 10
            strengths.append("Başlık uzunluğu ideal aralıkta.")
        elif title_word_count < 6:
            score += 3
            issues.append("Başlık çok kısa — anahtar kelimeleri artır (8-15 kelime ideal).")
        elif title_word_count > 20:
            score += 5
            issues.append("Başlık çok uzun — arama algoritması ilk 10 kelimeye ağırlık verir.")
    else:
        score += 5  # Bilgi yoksa orta puan

    # Değerlendirmeler (10 puan)
    if review_count >= 50 and avg_rating >= 4.8:
        score += 10
        strengths.append(f"{review_count} değerlendirme, {avg_rating:.1f} ortalama — güçlü sosyal kanıt.")
    elif review_count >= 10 and avg_rating >= 4.5:
        score += 7
    elif review_count >= 3:
        score += 4
    else:
        issues.append("Yorum sayısı az — müşterilere yorum bırakmaları için teşvik et.")

    score = min(score, 100)

    if score >= 80:
        grade: Literal["poor", "average", "good", "excellent"] = "excellent"
        recommendation = "Listing çok güçlü. Reklam verimli olacak — bütçeyi artırmayı düşün."
    elif score >= 60:
        grade = "good"
        recommendation = "Listing iyi durumda. Küçük iyileştirmelerle reklam verimini artırabilirsin."
    elif score >= 40:
        grade = "average"
        recommendation = "Listing ortalama. Reklamdan önce fotoğraf ve başlığı iyileştir."
    else:
        grade = "poor"
        recommendation = "Listing zayıf. Reklamdan önce ciddi revizyon gerekiyor — şu an harcama israfı olur."

    return ListingQualityResult(
        score=score,
        grade=grade,
        ctr_ratio=round(ctr_ratio, 2),
        product_ctr=round(product_ctr, 4),
        category_avg_ctr=round(bench, 4),
        category=category,
        recommendation=recommendation,
        issues=issues,
        strengths=strengths,
    )


# ─── Ürün Yaşam Döngüsü ──────────────────────────────────────────────────────

@dataclass
class LifecycleResult:
    stage: Literal["launch", "growth", "mature", "declining"]
    label: str
    confidence: Literal["low", "medium", "high"]
    roas_trend_pct: float          # Son 14 gün vs önceki 14 gün, %
    ema_7d: float
    ema_30d: float
    days_with_data: int
    recommendation: str
    next_action: str


def detect_product_lifecycle(
    roas_history: list[float],    # Günlük ROAS listesi (kronolojik, en eski → en yeni)
    seasonal_index: float = 0.5,  # 0-1: 1 = yoğun sezon
) -> LifecycleResult:
    """
    Ürünün yaşam döngüsü evresini belirler.
    launch → growth → mature → declining
    """
    n = len(roas_history)

    if n < 7:
        return LifecycleResult(
            stage="launch", label="Başlangıç",
            confidence="low",
            roas_trend_pct=0.0, ema_7d=0.0, ema_30d=0.0,
            days_with_data=n,
            recommendation="Yeterli veri yok. 14 gün daha bekle, ardından analiz et.",
            next_action="Veri toplamaya devam et.",
        )

    # EMA hesapla
    def ema(values: list[float], period: int) -> float:
        k = 2 / (period + 1)
        result = values[0]
        for v in values[1:]:
            result = v * k + result * (1 - k)
        return result

    ema_7 = ema(roas_history[-min(30, n):], 7)
    ema_30 = ema(roas_history[-min(90, n):], 30) if n >= 30 else ema(roas_history, n)

    # Son 14 gün vs önceki 14 gün trend
    if n >= 28:
        recent_14 = sum(roas_history[-14:]) / 14
        prev_14 = sum(roas_history[-28:-14]) / 14
        trend_pct = ((recent_14 - prev_14) / max(prev_14, 0.01)) * 100
    elif n >= 14:
        recent_7 = sum(roas_history[-7:]) / 7
        first_7 = sum(roas_history[:7]) / 7
        trend_pct = ((recent_7 - first_7) / max(first_7, 0.01)) * 100
    else:
        trend_pct = 0.0

    # Evre tespiti
    if n < 30:
        stage: Literal["launch", "growth", "mature", "declining"] = "launch"
        label = "Başlangıç"
        confidence: Literal["low", "medium", "high"] = "low"
        recommendation = "Ürün yeni. İlk 30 günde çok yorumlama yapma, veri biriktir."
        next_action = "14 gün daha bekle, sonra trend analizi yap."
    elif trend_pct > 5 and ema_7 > ema_30 * 0.95:
        stage = "growth"
        label = "Büyüme"
        confidence = "medium" if n < 60 else "high"
        recommendation = "ROAS artıyor. Bütçeyi agresif artır, momentumu yakala."
        next_action = "Bütçeyi %20-30 artır. 7 günde bir kontrol et."
    elif trend_pct < -10 and ema_7 < ema_30 * 0.9 and seasonal_index < 0.4:
        stage = "declining"
        label = "Düşüş"
        confidence = "medium"
        recommendation = "ROAS düşüyor ve sezon baskısı yok. Listing yenile veya reklamı durdur."
        next_action = "Listing'i güncelle (fotoğraf, başlık, fiyat). 14 gün bekle, iyileşmezse durdur."
    elif trend_pct < -10 and seasonal_index >= 0.4:
        stage = "declining"
        label = "Sezonsal Düşüş"
        confidence = "medium"
        recommendation = "Düşüş büyük ihtimalle mevsimsel. Sezon dönene kadar bütçeyi azalt."
        next_action = "Bütçeyi %40 azalt. Yoğun sezon öncesi tekrar değerlendir."
    else:
        stage = "mature"
        label = "Olgunluk"
        confidence = "high" if n >= 60 else "medium"
        recommendation = "Stabil seyir. Mevcut bütçeyi koru, küçük optimizasyonlar yap."
        next_action = "A/B test: farklı anahtar kelime grubu veya bütçe zamanlaması dene."

    return LifecycleResult(
        stage=stage,
        label=label,
        confidence=confidence,
        roas_trend_pct=round(trend_pct, 1),
        ema_7d=round(ema_7, 3),
        ema_30d=round(ema_30, 3),
        days_with_data=n,
        recommendation=recommendation,
        next_action=next_action,
    )


# ─── Strateji Projeksiyon (Erken Uyarı) ──────────────────────────────────────

@dataclass
class StrategyProjection:
    current_progress_pct: float
    projected_completion_day: int   # Kaçıncı günde hedefe ulaşılır (tahmin)
    will_meet_deadline: bool
    days_remaining: int
    velocity: float                  # Günlük ilerleme hızı (%/gün)
    warning: str | None
    confidence: Literal["low", "medium", "high"]


def project_strategy_outcome(
    checkpoints: list[dict],         # [{"day": 3, "progress_pct": 40}, ...]
    target_date_days: int,           # Toplam süre (gün)
    days_elapsed: int,
) -> StrategyProjection:
    """
    Mevcut checkpoint verisiyle lineer ekstrapolasyon.
    "Bu hızla giderse hedefe kaç günde ulaşılır?"
    """
    days_remaining = max(0, target_date_days - days_elapsed)

    if not checkpoints or days_elapsed == 0:
        return StrategyProjection(
            current_progress_pct=0, projected_completion_day=target_date_days,
            will_meet_deadline=True, days_remaining=days_remaining,
            velocity=0, warning=None, confidence="low",
        )

    current_pct = checkpoints[-1].get("progress_pct", 0)

    # Lineer regresyon: (gün, ilerleme) çiftleri
    if len(checkpoints) >= 2:
        days_list = [cp.get("day", i * 3) for i, cp in enumerate(checkpoints)]
        pct_list = [cp.get("progress_pct", 0) for cp in checkpoints]
        n = len(days_list)
        sum_x = sum(days_list)
        sum_y = sum(pct_list)
        sum_xy = sum(x * y for x, y in zip(days_list, pct_list))
        sum_x2 = sum(x * x for x in days_list)
        denom = n * sum_x2 - sum_x ** 2
        velocity = (n * sum_xy - sum_x * sum_y) / denom if abs(denom) > 1e-9 else 0
    else:
        velocity = current_pct / max(days_elapsed, 1)

    velocity = max(0.0, velocity)

    # %100'e ulaşmak için gereken gün
    remaining_pct = max(0, 100 - current_pct)
    if velocity > 0:
        days_to_complete = remaining_pct / velocity
        projected_day = days_elapsed + days_to_complete
    else:
        projected_day = target_date_days * 2  # Çok uzun

    will_meet = projected_day <= target_date_days

    # Uyarı mesajı
    warning = None
    if not will_meet:
        overshoot = projected_day - target_date_days
        warning = (
            f"Mevcut hızda hedefe {projected_day:.0f}. günde ulaşırsın "
            f"(hedef: {target_date_days}. gün). {overshoot:.0f} gün geç."
        )
    elif projected_day < target_date_days * 0.7:
        warning = None  # Erken bitecek — iyi haber

    confidence: Literal["low", "medium", "high"] = (
        "high" if len(checkpoints) >= 3 else
        "medium" if len(checkpoints) == 2 else "low"
    )

    return StrategyProjection(
        current_progress_pct=round(current_pct, 1),
        projected_completion_day=round(projected_day),
        will_meet_deadline=will_meet,
        days_remaining=days_remaining,
        velocity=round(velocity, 2),
        warning=warning,
        confidence=confidence,
    )


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
