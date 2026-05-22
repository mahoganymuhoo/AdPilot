from pydantic import BaseModel, EmailStr
from typing import Literal


class SellerCreate(BaseModel):
    email: EmailStr
    password: str
    shop_name: str | None = None
    ai_provider: Literal["claude", "openai"] = "claude"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    default_cogs_percent: float = 0.40
    target_roas: float = 3.0
    target_acos: float = 30.0
    daily_budget: float = 10.0


class SellerUpdate(BaseModel):
    shop_name: str | None = None
    ai_provider: Literal["claude", "openai"] | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    default_cogs_percent: float | None = None
    target_roas: float | None = None
    target_acos: float | None = None
    daily_budget: float | None = None


class SellerRead(BaseModel):
    id: int
    email: str
    shop_name: str | None
    ai_provider: str
    default_cogs_percent: float
    target_roas: float
    target_acos: float
    daily_budget: float

    model_config = {"from_attributes": True}
