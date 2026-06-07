from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0

    @field_validator("sku")
    @classmethod
    def sku_must_not_be_empty(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("SKU cannot be empty")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("stock")
    @classmethod
    def stock_must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stock must be >= 0")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("stock")
    @classmethod
    def stock_must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Stock must be >= 0")
        return v


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int
