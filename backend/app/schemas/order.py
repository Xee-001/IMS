from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    customer_id: str
    product_id: str
    quantity: int = Field(gt=0, description="Must be greater than 0")


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    product_id: str
    quantity: int
    total_price: float
    created_at: datetime
