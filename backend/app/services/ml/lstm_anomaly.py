"""
LSTM Anomali Tespiti — Z-score Hibrit Model

Strateji:
- Az veri (< 60 gün): Z-score kullan (hızlı, parametresiz)
- Yeterli veri (≥ 60 gün): Saf Python LSTM (NumPy ile, PyTorch bağımlılığı yok)

LSTM mantığı:
1. Son 30 günü eğitim penceresi olarak kullan
2. Bir sonraki günü tahmin et
3. Tahmin hatası (|gerçek - tahmin|) yüksekse anomali

PyTorch bağımlılığı olmadan saf NumPy LSTM: sigmoid + tanh aktivasyonlar,
manuel forward pass. Production'da torch.nn.LSTM ile değiştirilebilir.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal


# ─── Veri Yapıları ───────────────────────────────────────────────────────────

@dataclass
class AnomalyScore:
    index: int           # Zaman serisindeki pozisyon
    value: float         # Gözlemlenen değer
    score: float         # Anomali skoru (0-1 arası)
    is_anomaly: bool
    method: Literal["z_score", "lstm"]
    z_score: float | None = None
    lstm_error: float | None = None
    severity: Literal["low", "medium", "high", "critical"] = "low"
    direction: Literal["up", "down"] = "up"


@dataclass
class AnomalyDetectionResult:
    series_length: int
    anomalies: list[AnomalyScore]
    method_used: Literal["z_score", "lstm", "hybrid"]
    threshold_used: float
    anomaly_count: int
    summary: str


# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

def _zscore_anomalies(
    values: list[float],
    threshold: float = 2.5,
) -> list[AnomalyScore]:
    """Kayan ortalama + std ile Z-score anomali tespiti."""
    n = len(values)
    window = min(30, n)
    results: list[AnomalyScore] = []

    for i in range(window, n):
        window_vals = values[max(0, i - window):i]
        mean = sum(window_vals) / len(window_vals)
        variance = sum((v - mean) ** 2 for v in window_vals) / len(window_vals)
        std = math.sqrt(variance) if variance > 0 else 1e-9

        z = (values[i] - mean) / std
        is_anom = abs(z) > threshold
        severity: Literal["low", "medium", "high", "critical"] = (
            "critical" if abs(z) > 4.0 else
            "high" if abs(z) > 3.0 else
            "medium" if abs(z) > 2.5 else "low"
        )
        results.append(AnomalyScore(
            index=i, value=values[i],
            score=min(1.0, abs(z) / (threshold * 2)),
            is_anomaly=is_anom,
            method="z_score",
            z_score=round(z, 3),
            severity=severity if is_anom else "low",
            direction="up" if values[i] > mean else "down",
        ))

    return results


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))


def _tanh(x: float) -> float:
    return math.tanh(max(-500, min(500, x)))


class _MiniLSTM:
    """
    Tek hücrelik saf Python LSTM.
    h_size: gizli durum boyutu (küçük tutulur — 4-8 yeterli)

    Eğitim: gradient descent ile değil, basit online öğrenme (running stats).
    Bu model anomali için yeterli — kesin tahmin gerekmez, sadece "olağandışı mı?" sorusu.
    """
    def __init__(self, h_size: int = 4, lr: float = 0.01):
        self.h = h_size
        self.lr = lr
        # Ağırlıklar: (input_dim=1 + h_size → h_size) × 4 kapı
        # Xavier init
        scale = 1.0 / math.sqrt(1 + h_size)
        self._Wf = [scale * (2 * ((i * 7 + 3) % 100) / 100 - 1) for i in range(h_size)]
        self._Wi = [scale * (2 * ((i * 11 + 5) % 100) / 100 - 1) for i in range(h_size)]
        self._Wg = [scale * (2 * ((i * 13 + 7) % 100) / 100 - 1) for i in range(h_size)]
        self._Wo = [scale * (2 * ((i * 17 + 11) % 100) / 100 - 1) for i in range(h_size)]
        self._Wy = [scale * (2 * ((i * 19 + 13) % 100) / 100 - 1) for i in range(h_size)]
        self._by = 0.0
        self._h_prev = [0.0] * h_size
        self._c_prev = [0.0] * h_size

    def _forward(self, x: float) -> tuple[float, list[float], list[float]]:
        h, c_prev, h_prev = self.h, self._c_prev, self._h_prev
        f = [_sigmoid(self._Wf[i] * x + h_prev[i]) for i in range(h)]
        i_ = [_sigmoid(self._Wi[i] * x + h_prev[i]) for i in range(h)]
        g = [_tanh(self._Wg[i] * x + h_prev[i]) for i in range(h)]
        o = [_sigmoid(self._Wo[i] * x + h_prev[i]) for i in range(h)]
        c_new = [f[i] * c_prev[i] + i_[i] * g[i] for i in range(h)]
        h_new = [o[i] * _tanh(c_new[i]) for i in range(h)]
        y_pred = sum(self._Wy[i] * h_new[i] for i in range(h)) + self._by
        return y_pred, h_new, c_new

    def step(self, x: float, y_true: float | None = None) -> float:
        """Forward pass. y_true verilirse ağırlıkları günceller (online öğrenme)."""
        y_pred, h_new, c_new = self._forward(x)
        if y_true is not None:
            err = y_pred - y_true
            for i in range(self.h):
                self._Wy[i] -= self.lr * err * h_new[i]
            self._by -= self.lr * err
        self._h_prev, self._c_prev = h_new, c_new
        return y_pred

    def predict(self, x: float) -> float:
        y, h_new, c_new = self._forward(x)
        self._h_prev, self._c_prev = h_new, c_new
        return y


def _lstm_anomalies(
    values: list[float],
    train_ratio: float = 0.6,
    error_threshold_sigma: float = 2.5,
) -> list[AnomalyScore]:
    """
    LSTM ile anomali tespiti:
    1. İlk %60: modeli eğit (her adımda online güncelleme)
    2. Son %40: tahmin et, hata büyükse anomali işaretle
    """
    n = len(values)
    train_end = int(n * train_ratio)

    # Normalize (0-1 arası)
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1.0
    norm = [(v - mn) / rng for v in values]

    model = _MiniLSTM(h_size=6, lr=0.05)

    # Eğitim fazı
    for i in range(train_end - 1):
        model.step(norm[i], y_true=norm[i + 1])

    # Tahmin fazı — hataları topla (threshold için)
    errors: list[float] = []
    preds: list[float] = []
    for i in range(train_end - 1, n - 1):
        pred = model.predict(norm[i])
        err = abs(norm[i + 1] - pred)
        errors.append(err)
        preds.append(pred)

    if not errors:
        return []

    mean_err = sum(errors) / len(errors)
    var_err = sum((e - mean_err) ** 2 for e in errors) / len(errors)
    std_err = math.sqrt(var_err) if var_err > 0 else 1e-9

    results: list[AnomalyScore] = []
    for idx, err in enumerate(errors):
        real_idx = train_end + idx
        z = (err - mean_err) / std_err
        is_anom = z > error_threshold_sigma
        severity: Literal["low", "medium", "high", "critical"] = (
            "critical" if z > 4.0 else
            "high" if z > 3.0 else
            "medium" if z > 2.5 else "low"
        )
        actual = values[real_idx]
        predicted_real = preds[idx] * rng + mn
        results.append(AnomalyScore(
            index=real_idx,
            value=actual,
            score=min(1.0, max(0.0, z / (error_threshold_sigma * 2))),
            is_anomaly=is_anom,
            method="lstm",
            lstm_error=round(err, 4),
            z_score=round(z, 3),
            severity=severity if is_anom else "low",
            direction="up" if actual > predicted_real else "down",
        ))

    return results


# ─── Ana Dispatcher ──────────────────────────────────────────────────────────

def detect_anomalies(
    values: list[float],
    threshold: float = 2.5,
    min_lstm_points: int = 60,
) -> AnomalyDetectionResult:
    """
    Hibrit anomali tespiti.

    - values: ROAS, ACOS veya başka bir zaman serisi
    - threshold: Z-score / LSTM hata için eşik (varsayılan 2.5)
    - min_lstm_points: LSTM'e geçmek için minimum veri noktası

    Yeterli veri varsa LSTM, yoksa Z-score kullanır.
    """
    n = len(values)

    if n < 10:
        return AnomalyDetectionResult(
            series_length=n, anomalies=[], method_used="z_score",
            threshold_used=threshold, anomaly_count=0,
            summary="Yeterli veri yok (en az 10 gün gerekli).",
        )

    if n >= min_lstm_points:
        scores = _lstm_anomalies(values, error_threshold_sigma=threshold)
        method: Literal["z_score", "lstm", "hybrid"] = "lstm"
    else:
        scores = _zscore_anomalies(values, threshold=threshold)
        method = "z_score"

    anomalies = [s for s in scores if s.is_anomaly]
    high_count = sum(1 for a in anomalies if a.severity in ("high", "critical"))

    if anomalies:
        summary = (
            f"{len(anomalies)} anomali tespit edildi ({high_count} yüksek/kritik). "
            f"Yöntem: {method}. Eşik: {threshold}σ."
        )
    else:
        summary = f"Anomali tespit edilmedi. {n} veri noktası analiz edildi ({method})."

    return AnomalyDetectionResult(
        series_length=n,
        anomalies=anomalies,
        method_used=method,
        threshold_used=threshold,
        anomaly_count=len(anomalies),
        summary=summary,
    )
