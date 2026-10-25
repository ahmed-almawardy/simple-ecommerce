from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    description: str
    price_cents: int
    category: str
    image_url: str
    is_featured: bool
    stock: int

class CartQuantity(BaseModel):
    quantity: int = Field(ge=0, le=20)

class CartAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)

class CheckoutInput(BaseModel):
    shipping_name: str = Field(min_length=2, max_length=120)
    shipping_address: str = Field(min_length=5, max_length=500)
    shipping_phone: str = Field(min_length=7, max_length=40)
    shipping_city: str = Field(min_length=2, max_length=100)
    shipping_country: str = Field(default="EG", min_length=2, max_length=8)

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_slug: str
    image_url: str
    price_cents: int
    quantity: int

class OrderOut(BaseModel):
    id: int
    amount_cents: int
    currency: str
    status: str
    shipping_name: str
    shipping_address: str
    shipping_phone: str
    shipping_city: str
    shipping_country: str
    payment_provider: str
    created_at: datetime
    paid_at: datetime | None = None
    items: list[OrderItemOut]
