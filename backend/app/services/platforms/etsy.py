"""
Etsy Platform Adapter

Open API v3 kullanır. Promoted Listings API yoktur — dolaylı ROAS hesabı yapılır.
Receipts + transactions + shop stats → platform-agnostic ProductMetrics.
"""
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from app.services.platforms.base import PlatformAdapter, ProductMetrics, SyncResult

ETSY_API_BASE = "https://openapi.etsy.com/v3/application"


class EtsyAdapter(PlatformAdapter):
    PLATFORM_NAME = "etsy"
    PLATFORM_FEE_PCT = 0.065      # %6.5 işlem ücreti
    PLATFORM_LISTING_FEE = 0.20  # $0.20 listeleme

    def _validate_credentials(self) -> None:
        required = {"access_token", "shop_id", "api_key"}
        missing = required - set(self.credentials)
        if missing:
            raise ValueError(f"Etsy credentials eksik alanlar: {missing}")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.credentials['access_token']}",
            "x-api-key": self.credentials["api_key"],
        }

    async def get_products(self, seller_id: str) -> list[dict]:
        """Aktif Etsy listing'lerini döndür."""
        shop_id = self.credentials["shop_id"]
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{ETSY_API_BASE}/shops/{shop_id}/listings/active",
                headers=self._headers(),
                params={"limit": 100},
            )
            r.raise_for_status()
            data = r.json()

        return [
            {
                "listing_id": str(l["listing_id"]),
                "title": l.get("title", ""),
                "price": float(l.get("price", {}).get("amount", 0)) / 100,
                "quantity": l.get("quantity", 0),
                "tags": l.get("tags", []),
                "category": l.get("taxonomy_path", [""])[0] if l.get("taxonomy_path") else None,
                "views": l.get("views", 0),
                "platform": "etsy",
            }
            for l in data.get("results", [])
        ]

    async def get_metrics(
        self,
        listing_ids: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> list[ProductMetrics]:
        """
        Etsy'nin Promoted Listings API'si olmadığı için
        receipt/transaction verisinden dolaylı ROAS hesabı yapar.
        """
        shop_id = self.credentials["shop_id"]
        min_created = int(start_date.timestamp())
        metrics_map: dict[str, ProductMetrics] = {}

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{ETSY_API_BASE}/shops/{shop_id}/receipts",
                headers=self._headers(),
                params={
                    "min_created": min_created,
                    "limit": 100,
                    "sort_on": "created",
                },
            )
            r.raise_for_status()
            receipts = r.json().get("results", [])

        for receipt in receipts:
            created = datetime.fromtimestamp(receipt.get("create_timestamp", 0), tz=timezone.utc)
            for txn in receipt.get("transactions", []):
                lid = str(txn.get("listing_id", ""))
                if lid not in listing_ids:
                    continue
                revenue = float(txn.get("price", {}).get("amount", 0)) / 100 * txn.get("quantity", 1)
                if lid not in metrics_map:
                    metrics_map[lid] = ProductMetrics(
                        listing_id=lid,
                        title=txn.get("title", ""),
                        date=created,
                        revenue=0.0, conversions=0,
                    )
                metrics_map[lid].revenue += revenue
                metrics_map[lid].conversions += 1

        return list(metrics_map.values())

    async def sync(self, seller_id: str, days_back: int = 1) -> SyncResult:
        """Son N günlük veri çekimi — Celery task tarafından çağrılır."""
        try:
            products = await self.get_products(seller_id)
            listing_ids = [p["listing_id"] for p in products]

            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days_back)
            metrics = await self.get_metrics(listing_ids, start, end)

            return SyncResult(
                platform="etsy",
                success=True,
                products_synced=len(products),
                metrics_saved=len(metrics),
            )
        except httpx.HTTPStatusError as e:
            rate_remaining = None
            if e.response.status_code == 429:
                rate_remaining = 0
            return SyncResult(
                platform="etsy",
                success=False,
                products_synced=0,
                metrics_saved=0,
                errors=[f"HTTP {e.response.status_code}: {e.response.text[:200]}"],
                rate_limit_remaining=rate_remaining,
            )
        except Exception as e:
            return SyncResult(
                platform="etsy",
                success=False,
                products_synced=0,
                metrics_saved=0,
                errors=[str(e)],
            )
