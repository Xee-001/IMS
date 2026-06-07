from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.response import APIResponse
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=APIResponse[List[CustomerResponse]])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    customers = await customer_service.get_all_customers(db, skip, limit)
    return APIResponse(data=[CustomerResponse.model_validate(c) for c in customers])


@router.get("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    customer = await customer_service.get_customer_by_id(db, customer_id)
    return APIResponse(data=CustomerResponse.model_validate(customer))


@router.post("/", response_model=APIResponse[CustomerResponse], status_code=201)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    customer = await customer_service.create_customer(db, data)
    return APIResponse(data=CustomerResponse.model_validate(customer))


@router.put("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
):
    customer = await customer_service.update_customer(db, customer_id, data)
    return APIResponse(data=CustomerResponse.model_validate(customer))


@router.delete("/{customer_id}", response_model=APIResponse[None])
async def delete_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    await customer_service.delete_customer(db, customer_id)
    return APIResponse(data=None)
