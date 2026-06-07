from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.response import APIResponse
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=APIResponse[List[OrderResponse]])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    orders = await order_service.get_all_orders(db, skip, limit)
    return APIResponse(data=[OrderResponse.model_validate(o) for o in orders])


@router.get("/{order_id}", response_model=APIResponse[OrderResponse])
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    order = await order_service.get_order_by_id(db, order_id)
    return APIResponse(data=OrderResponse.model_validate(order))


@router.post("/", response_model=APIResponse[OrderResponse], status_code=201)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = await order_service.create_order(db, data)
    return APIResponse(data=OrderResponse.model_validate(order))
