from pydantic import BaseModel


class ProductCreate(BaseModel):
    platform_id: int
    listing_id: str | None = None
    title: str
    description: str | None = None
    url: str | None = None
    image_url: str | None = None
    cogs: float | None = None
    shipping_cost: float = 0.0
    price: float | None = None
    inventory: int = 0


class ProductUpdate(BaseModel):
    title: str | None = None
    cogs: float | None = None
    shipping_cost: float | None = None
    price: float | None = None
    inventory: int | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    seller_id: int
    platform_id: int
    listing_id: str | None
    title: str
    url: str | None
    image_url: str | None
    cogs: float | None
    shipping_cost: float
    price: float | None
    inventory: int
    is_active: bool

    model_config = {"from_attributes": True}
