"""
Platform Adapter Interface

Her e-ticaret platformu bu interface'i uygular.
Sistem platform-agnostic kalmak için sadece bu interface'e bağımlıdır.

Desteklenen platformlar:
- Etsy (birincil, tam implementasyon)
- Amazon SP-API (taslak)
- Shopify (taslak)
- TikTok Shop (gelecek)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProductMetrics:
    """Platform-agnostic ürün metrik yapısı."""
    listing_id: str                  # Platform'a özel ürün ID
    title: str
    date: datetime

    # Reklam metrikleri
    impressions: int = 0
    clicks: int = 0
    ad_spend: float = 0.0
    revenue: float = 0.0
    conversions: int = 0
    views: int = 0

    # Hesaplananlar (None = veri yetersiz)
    roas: float | None = None
    acos: float | None = None
    ctr: float | None = None

    # Ürün bilgisi
    price: float | None = None
    inventory: int | None = None
    category: str | None = None

    # Platform'a özel ek veri
    raw: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    """Bir sync işleminin özeti."""
    platform: str
    success: bool
    products_synced: int
    metrics_saved: int
    errors: list[str] = field(default_factory=list)
    last_sync_at: datetime = field(default_factory=datetime.utcnow)
    rate_limit_remaining: int | None = None


class PlatformAdapter(ABC):
    """
    Tüm platform adapter'larının uyguladığı interface.

    Her platform için credentials yapısı farklıdır:
    - Etsy: {"api_key": ..., "access_token": ..., "shop_id": ...}
    - Amazon: {"access_key": ..., "secret_key": ..., "seller_id": ..., "marketplace_id": ...}
    - Shopify: {"shop_domain": ..., "access_token": ...}
    """
    PLATFORM_NAME: str = "unknown"
    PLATFORM_FEE_PCT: float = 0.0        # İşlem ücreti yüzdesi
    PLATFORM_LISTING_FEE: float = 0.0    # Listeleme başına sabit ücret

    def __init__(self, credentials: dict):
        self.credentials = credentials
        self._validate_credentials()

    @abstractmethod
    def _validate_credentials(self) -> None:
        """Gerekli credential alanlarının varlığını doğrula."""
        ...

    @abstractmethod
    async def get_products(self, seller_id: str) -> list[dict]:
        """Platform'daki aktif ürün listesini döndür."""
        ...

    @abstractmethod
    async def get_metrics(
        self,
        listing_ids: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> list[ProductMetrics]:
        """
        Belirtilen ürünler için tarih aralığındaki reklam metriklerini döndür.
        Veri yoksa boş liste döner (exception fırlatmaz).
        """
        ...

    @abstractmethod
    async def sync(self, seller_id: str, days_back: int = 1) -> SyncResult:
        """
        Celery task tarafından çağrılır. Son N günün verilerini çekip kaydeder.
        Rate limiting ve retry bu metod içinde yönetilir.
        """
        ...

    def calculate_fees(self, price: float, quantity: int = 1) -> dict:
        """
        Bu platformda satışın fee maliyetini hesapla.
        Her platform kendi sabitlerini override eder.
        """
        transaction_fee = price * self.PLATFORM_FEE_PCT * quantity
        listing_fee = self.PLATFORM_LISTING_FEE
        return {
            "transaction_fee": round(transaction_fee, 4),
            "listing_fee": round(listing_fee, 4),
            "total_fee": round(transaction_fee + listing_fee, 4),
            "fee_pct": self.PLATFORM_FEE_PCT * 100,
        }

    def break_even_acos(self, price: float, cogs: float, shipping: float = 0.0) -> float:
        """Platform ücretleri dahil break-even ACOS hesabı."""
        fees = self.calculate_fees(price)
        net = price - cogs - shipping - fees["total_fee"]
        return round((net / price) * 100, 2) if price > 0 else 0.0

    @property
    def platform_info(self) -> dict:
        return {
            "name": self.PLATFORM_NAME,
            "fee_pct": self.PLATFORM_FEE_PCT * 100,
            "listing_fee": self.PLATFORM_LISTING_FEE,
        }
