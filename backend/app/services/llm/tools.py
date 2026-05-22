"""
Claude Tool Use — Tool şema tanımları ve tip aliasleri.

Claude, analiz sırasında bu tool'ları çağırarak kendi ihtiyacı olan
veriyi sorgular. Tool handler'ları (gerçek DB sorgusu) API katmanında
ToolExecutor callable olarak enjekte edilir.
"""
from typing import Callable, Awaitable, Any

ToolExecutor = Callable[[str, dict], Awaitable[dict]]

TOOLS: list[dict] = [
    {
        "name": "get_roas_trend",
        "description": (
            "Bir ürünün son N günlük günlük ROAS trend verisini getirir. "
            "EMA_7 ve EMA_30 değerleri dahildir. "
            "Trend analizi yapmak, iyileşme/kötüleşme tespiti için kullan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "Ürün ID"},
                "days": {
                    "type": "integer",
                    "description": "Kaç günlük veri (varsayılan: 30)",
                    "default": 30,
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_product_metrics",
        "description": (
            "Bir ürünün güncel KPI metriklerini döndürür: "
            "ROAS, ACOS, CTR, dönüşüm sayısı, reklam harcaması, gelir, "
            "kâr marjı, break-even ACOS. "
            "Detaylı karlılık analizi için kullan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "Ürün ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_anomalies",
        "description": (
            "Satıcının son 7 günde tespit edilen anomalilerini getirir. "
            "Her anomali: metrik, z-score, şiddet (critical/high/medium/low), "
            "yön (up/down), ürün bilgisi içerir. "
            "Acil durumları ve dikkat gereken metrikleri belirlemek için kullan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seller_id": {"type": "integer", "description": "Satıcı ID"},
                "unread_only": {
                    "type": "boolean",
                    "description": "Sadece okunmamış anomaliler (varsayılan: false)",
                    "default": False,
                },
            },
            "required": ["seller_id"],
        },
    },
    {
        "name": "get_budget_allocation",
        "description": (
            "Satıcının mevcut günlük bütçe dağılımını ve ürün bazlı "
            "reklam harcamalarını döndürür. "
            "Bütçe optimizasyonu, dağılım analizi için kullan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seller_id": {"type": "integer", "description": "Satıcı ID"},
            },
            "required": ["seller_id"],
        },
    },
    {
        "name": "get_strategy_history",
        "description": (
            "Bir ürün veya satıcının geçmiş strateji sonuçlarını getirir. "
            "Başarı oranı, ortalama ROAS değişimi, en çok hangi tür stratejinin "
            "işe yaradığını görmek için kullan. "
            "Yeni strateji önerisini geçmiş verilerle desteklemek için kullan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seller_id": {"type": "integer", "description": "Satıcı ID"},
                "product_id": {
                    "type": "integer",
                    "description": "Ürün ID (opsiyonel — verilmezse tüm ürünler)",
                },
            },
            "required": ["seller_id"],
        },
    },
]
