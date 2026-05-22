"""
Shopify Adapter (Taslak)

Shopify Admin GraphQL API + Marketing Events entegrasyonu.
Shopify reklam verisini doğrudan sunmaz — Meta/Google Ads entegrasyonu ayrıca gerekir.

Referans: https://shopify.dev/api/admin-graphql
"""
import httpx
from datetime import datetime, timezone, timedelta
from app.services.platforms.base import PlatformAdapter, ProductMetrics, SyncResult


class ShopifyAdapter(PlatformAdapter):
    PLATFORM_NAME = "shopify"
    PLATFORM_FEE_PCT = 0.02       # Shopify Payments: %2 (plan bağımlı)
    PLATFORM_LISTING_FEE = 0.0   # Listeleme ücreti yok

    def _validate_credentials(self) -> None:
        required = {"shop_domain", "access_token"}
        missing = required - set(self.credentials)
        if missing:
            raise ValueError(f"Shopify credentials eksik alanlar: {missing}")

    def _api_url(self) -> str:
        domain = self.credentials["shop_domain"].rstrip("/")
        if not domain.startswith("https://"):
            domain = f"https://{domain}"
        return f"{domain}/admin/api/2024-01"

    def _headers(self) -> dict:
        return {
            "X-Shopify-Access-Token": self.credentials["access_token"],
            "Content-Type": "application/json",
        }

    async def get_products(self, seller_id: str) -> list[dict]:
        """
        Shopify Admin API → aktif ürün listesi.

        Gerçek implementasyon: GET /admin/api/2024-01/products.json
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self._api_url()}/products.json",
                    headers=self._headers(),
                    params={"status": "active", "limit": 250},
                )
                r.raise_for_status()
                data = r.json()

            return [
                {
                    "listing_id": str(p["id"]),
                    "title": p.get("title", ""),
                    "price": float(p.get("variants", [{}])[0].get("price", 0)) if p.get("variants") else 0.0,
                    "inventory": sum(
                        v.get("inventory_quantity", 0) for v in p.get("variants", [])
                    ),
                    "category": p.get("product_type", None),
                    "platform": "shopify",
                }
                for p in data.get("products", [])
            ]
        except Exception as e:
            return []

    async def get_metrics(
        self,
        listing_ids: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> list[ProductMetrics]:
        """
        Shopify Orders API → satış metrikleri.

        NOT: Shopify platformu reklam metriklerini (impressions, clicks, ROAS)
        doğrudan sunmaz. Reklam verileri için Meta Ads / Google Ads API
        entegrasyonu ayrıca gerekir. Şu an sadece order gelirini döner.

        Gerçek implementasyon: GET /orders.json + Marketing Events bağlantısı.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self._api_url()}/orders.json",
                    headers=self._headers(),
                    params={
                        "status": "any",
                        "created_at_min": start_date.isoformat(),
                        "created_at_max": end_date.isoformat(),
                        "limit": 250,
                        "fields": "id,created_at,line_items,total_price,financial_status",
                    },
                )
                r.raise_for_status()
                orders = r.json().get("orders", [])

            metrics_map: dict[str, ProductMetrics] = {}
            for order in orders:
                if order.get("financial_status") not in ("paid", "partially_paid"):
                    continue
                created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
                for item in order.get("line_items", []):
                    lid = str(item.get("product_id", ""))
                    if lid not in listing_ids:
                        continue
                    revenue = float(item.get("price", 0)) * item.get("quantity", 1)
                    if lid not in metrics_map:
                        metrics_map[lid] = ProductMetrics(
                            listing_id=lid, title=item.get("title", ""),
                            date=created, revenue=0.0, conversions=0,
                        )
                    metrics_map[lid].revenue += revenue
                    metrics_map[lid].conversions += item.get("quantity", 1)

            return list(metrics_map.values())

        except Exception:
            return []

    async def sync(self, seller_id: str, days_back: int = 1) -> SyncResult:
        try:
            products = await self.get_products(seller_id)
            listing_ids = [p["listing_id"] for p in products]
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days_back)
            metrics = await self.get_metrics(listing_ids, start, end)
            return SyncResult(
                platform="shopify",
                success=True,
                products_synced=len(products),
                metrics_saved=len(metrics),
                errors=["NOT: Shopify'da reklam metrikleri (ROAS/ACOS) için Meta/Google Ads entegrasyonu gereklidir."],
            )
        except Exception as e:
            return SyncResult(
                platform="shopify",
                success=False,
                products_synced=0,
                metrics_saved=0,
                errors=[str(e)],
            )

    def calculate_fees(self, price: float, quantity: int = 1) -> dict:
        """Shopify Payments transaction fee (plan bağımlı: Basic %2, Shopify %1, Advanced %0.5)."""
        txn_fee = price * self.PLATFORM_FEE_PCT * quantity
        return {
            "transaction_fee": round(txn_fee, 4),
            "listing_fee": 0.0,
            "total_fee": round(txn_fee, 4),
            "fee_pct": self.PLATFORM_FEE_PCT * 100,
            "note": "Shopify plan'a göre değişir: Basic %2, Shopify %1, Advanced %0.5",
        }
