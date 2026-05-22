from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.models.seller import Seller
from app.models.platform import Platform, PlatformConnection

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingSetupRequest(BaseModel):
    data_source: str  # api | csv | manual
    etsy_api_key: str | None = None
    etsy_shop_id: str | None = None
    cogs_default: float
    shipping_cost: float = 0.0
    target_roas: float = 3.0
    daily_budget: float = 30.0
    ai_provider: str = "claude"
    ai_api_key: str | None = None


@router.post("/setup")
async def setup_seller(req: OnboardingSetupRequest, db: AsyncSession = Depends(get_db)):
    """
    İlk kurulum: seller kaydı oluştur veya güncelle.
    Gerçek implementasyonda auth middleware'den seller_id alınır.
    Demo: seller_id=1 varsayılan.
    """
    result = await db.execute(select(Seller).where(Seller.id == 1))
    seller = result.scalar_one_or_none()

    if not seller:
        seller = Seller(
            id=1,
            shop_name="My Shop",
            platform="etsy",
            cogs_default=req.cogs_default,
            target_roas=req.target_roas,
            daily_budget=req.daily_budget,
            ai_provider=req.ai_provider,
        )
        db.add(seller)
    else:
        seller.cogs_default = req.cogs_default
        seller.target_roas = req.target_roas
        seller.daily_budget = req.daily_budget
        seller.ai_provider = req.ai_provider

    # TODO: API key'i şifrele (Fernet) — şimdilik boş bırak
    # seller.anthropic_api_key_enc = encrypt(req.ai_api_key) if req.ai_provider == "claude"

    # Platform bağlantısı
    if req.data_source == "api" and req.etsy_api_key:
        etsy_result = await db.execute(
            select(Platform).where(Platform.name == "etsy")
        )
        etsy_platform = etsy_result.scalar_one_or_none()
        if etsy_platform:
            conn_result = await db.execute(
                select(PlatformConnection).where(
                    PlatformConnection.seller_id == 1,
                    PlatformConnection.platform_id == etsy_platform.id,
                )
            )
            conn = conn_result.scalar_one_or_none()
            if not conn:
                conn = PlatformConnection(
                    seller_id=1,
                    platform_id=etsy_platform.id,
                    shop_id=req.etsy_shop_id or "",
                    data_mode="api",
                    access_token_enc=req.etsy_api_key,  # TODO: şifrele
                    is_active=True,
                )
                db.add(conn)
            else:
                conn.access_token_enc = req.etsy_api_key
                conn.data_mode = "api"
                conn.is_active = True

    await db.commit()

    return {
        "seller_id": 1,
        "data_source": req.data_source,
        "ai_provider": req.ai_provider,
        "target_roas": req.target_roas,
        "daily_budget": req.daily_budget,
        "status": "ok",
    }
