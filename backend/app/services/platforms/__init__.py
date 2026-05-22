from app.services.platforms.base import PlatformAdapter, ProductMetrics, SyncResult
from app.services.platforms.etsy import EtsyAdapter
from app.services.platforms.amazon import AmazonAdapter
from app.services.platforms.shopify import ShopifyAdapter


def get_platform_adapter(platform_name: str, credentials: dict) -> PlatformAdapter:
    """Platform adına göre doğru adapter'ı döndür."""
    adapters = {
        "etsy": EtsyAdapter,
        "amazon": AmazonAdapter,
        "shopify": ShopifyAdapter,
    }
    cls = adapters.get(platform_name.lower())
    if not cls:
        raise ValueError(f"Bilinmeyen platform: {platform_name}. Desteklenenler: {list(adapters)}")
    return cls(credentials)
