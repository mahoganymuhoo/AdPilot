"""
Amazon SP-API Adapter (Taslak)

Amazon Selling Partner API — Advertising + Orders entegrasyonu.
Gerçek API bağlantısı için credentials ve marketplace_id gereklidir.

Referans: https://developer-docs.amazon.com/sp-api/
"""
from datetime import datetime, timezone, timedelta
from app.services.platforms.base import PlatformAdapter, ProductMetrics, SyncResult


class AmazonAdapter(PlatformAdapter):
    PLATFORM_NAME = "amazon"
    PLATFORM_FEE_PCT = 0.15        # Ortalama Amazon referral fee ~%15
    PLATFORM_LISTING_FEE = 0.0     # FBA ayrıca ücretlendirilir

    # Marketplace ID → Bölge eşlemesi
    MARKETPLACE_REGIONS = {
        "ATVPDKIKX0DER": "us",          # amazon.com
        "A1F83G8C2ARO7P": "uk",          # amazon.co.uk
        "A1PA6795UKMFR9": "de",          # amazon.de
        "A13V1IB3VIYZZH": "fr",          # amazon.fr
        "APJ6JRA9NG5V4":  "it",          # amazon.it
        "A1RKKUPIHCS9HS": "es",          # amazon.es
    }

    def _validate_credentials(self) -> None:
        required = {"access_key", "secret_key", "seller_id", "marketplace_id"}
        missing = required - set(self.credentials)
        if missing:
            raise ValueError(f"Amazon credentials eksik alanlar: {missing}")

    async def get_products(self, seller_id: str) -> list[dict]:
        """
        Amazon Catalog API → aktif ASIN listesi.

        Gerçek implementasyon: SP-API CatalogItems endpoint.
        Şu an stub — API entegrasyonu Faz 5'te tamamlanacak.
        """
        # TODO: SP-API CatalogItems çağrısı
        # endpoint: GET /catalog/2022-04-01/items
        return [
            {
                "listing_id": "ASIN_STUB",
                "title": "Amazon ürün entegrasyonu yakında",
                "platform": "amazon",
                "note": "SP-API bağlantısı yapılandırılmamış",
            }
        ]

    async def get_metrics(
        self,
        listing_ids: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> list[ProductMetrics]:
        """
        Amazon Advertising API → Sponsored Products raporları.

        Gerçek implementasyon:
        - POST /v2/reports → rapport oluştur
        - GET /v2/reports/{reportId} → hazır olana kadar poll
        - Raporu indir ve parse et

        Şu an stub — report pipeline Faz 5'te eklenir.
        """
        # TODO: Amazon Advertising API report pipeline
        return []

    async def sync(self, seller_id: str, days_back: int = 1) -> SyncResult:
        """Amazon sync — şu an yapılandırılmamış durum bilgisi döner."""
        return SyncResult(
            platform="amazon",
            success=False,
            products_synced=0,
            metrics_saved=0,
            errors=["Amazon SP-API entegrasyonu henüz tamamlanmadı. Settings'ten credentials girin."],
        )

    def calculate_fees(self, price: float, quantity: int = 1) -> dict:
        """Amazon fee yapısı: referral fee + FBA fulfillment fee (basitleştirilmiş)."""
        referral_fee = price * self.PLATFORM_FEE_PCT * quantity
        fba_fee = 3.22 * quantity  # Ortalama FBA fulfillment fee (küçük-orta ürün)
        total = referral_fee + fba_fee
        return {
            "transaction_fee": round(referral_fee, 4),
            "fba_fee": round(fba_fee, 4),
            "listing_fee": 0.0,
            "total_fee": round(total, 4),
            "fee_pct": self.PLATFORM_FEE_PCT * 100,
        }
