from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.response import APIResponse
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=APIResponse[List[ProductResponse]])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    products = await product_service.get_all_products(db, skip, limit)
    return APIResponse(data=[ProductResponse.model_validate(p) for p in products])


@router.get("/{product_id}", response_model=APIResponse[ProductResponse])
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await product_service.get_product_by_id(db, product_id)
    return APIResponse(data=ProductResponse.model_validate(product))


@router.post("/", response_model=APIResponse[ProductResponse], status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = await product_service.create_product(db, data)
    return APIResponse(data=ProductResponse.model_validate(product))


@router.put("/{product_id}", response_model=APIResponse[ProductResponse])
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    product = await product_service.update_product(db, product_id, data)
    return APIResponse(data=ProductResponse.model_validate(product))


@router.delete("/{product_id}", response_model=APIResponse[None])
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    await product_service.delete_product(db, product_id)
    return APIResponse(data=None)
