"""
Etsy Open API v3 istemcisi.
Receipts, transactions ve shop stats endpoint'lerini kullanır.
Promoted Listings API yok — dolaylı ROAS hesabı yapılır.
"""
import httpx
from datetime import datetime, timezone
from app.core.config import settings


ETSY_API_BASE = "https://openapi.etsy.com/v3/application"


class EtsyClient:
    def __init__(self, access_token: str, shop_id: str):
        self.access_token = access_token
        self.shop_id = shop_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "x-api-key": settings.ETSY_API_KEY,
        }

    async def get_receipts(
        self,
        min_created: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Son siparişleri çeker. min_created: Unix timestamp."""
        params: dict = {"limit": limit, "offset": offset, "sort_on": "created", "sort_order": "desc"}
        if min_created:
            params["min_created"] = min_created

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{ETSY_API_BASE}/shops/{self.shop_id}/receipts",
                headers=self.headers,
                params=params,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    async def get_shop_listings(self, limit: int = 100, offset: int = 0) -> dict:
        """Aktif listing'leri çeker."""
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{ETSY_API_BASE}/shops/{self.shop_id}/listings/active",
                headers=self.headers,
                params={"limit": limit, "offset": offset},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    async def get_listing_inventory(self, listing_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{ETSY_API_BASE}/listings/{listing_id}/inventory",
                headers=self.headers,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    def normalize_receipt(self, receipt: dict) -> dict:
        """Etsy receipt'ini platform-agnostic formata çevirir."""
        return {
            "platform": "etsy",
            "transaction_id": str(receipt.get("receipt_id")),
            "created_at": datetime.fromtimestamp(
                receipt.get("create_timestamp", 0), tz=timezone.utc
            ).isoformat(),
            "revenue": float(receipt.get("grandtotal", {}).get("amount", 0)) / 100,
            "currency": receipt.get("grandtotal", {}).get("currency_code", "USD"),
            "buyer_country": receipt.get("country_iso", ""),
            "items": [
                {
                    "listing_id": str(t.get("listing_id")),
                    "title": t.get("title", ""),
                    "quantity": t.get("quantity", 1),
                    "price": float(t.get("price", {}).get("amount", 0)) / 100,
                }
                for t in receipt.get("transactions", [])
            ],
        }
