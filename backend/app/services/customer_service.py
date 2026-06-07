from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.core.exceptions import (
    CustomerInUseError,
    DuplicateCustomerCodeError,
    DuplicateEmailError,
    ResourceNotFoundError,
)


async def get_all_customers(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Customer]:
    result = await db.execute(select(Customer).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_customer_by_id(db: AsyncSession, customer_id: str) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise ResourceNotFoundError("Customer", customer_id)
    return customer


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    code_exists = await db.execute(
        select(Customer).where(Customer.customer_code == data.customer_code)
    )
    if code_exists.scalar_one_or_none():
        raise DuplicateCustomerCodeError(data.customer_code)

    email_exists = await db.execute(
        select(Customer).where(Customer.email == data.email)
    )
    if email_exists.scalar_one_or_none():
        raise DuplicateEmailError(data.email)

    customer = Customer(
        customer_code=data.customer_code,
        name=data.name,
        email=data.email,
        phone=data.phone,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def update_customer(
    db: AsyncSession, customer_id: str, data: CustomerUpdate
) -> Customer:
    customer = await get_customer_by_id(db, customer_id)

    if data.email is not None:
        email_exists = await db.execute(
            select(Customer).where(
                Customer.email == data.email, Customer.id != customer_id
            )
        )
        if email_exists.scalar_one_or_none():
            raise DuplicateEmailError(data.email)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(customer, field, value)

    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def delete_customer(db: AsyncSession, customer_id: str) -> None:
    customer = await get_customer_by_id(db, customer_id)

    from app.models.order import Order
    has_orders = await db.execute(
        select(Order.id).where(Order.customer_id == customer_id).limit(1)
    )
    if has_orders.scalar_one_or_none():
        raise CustomerInUseError(customer_id)

    await db.delete(customer)
    await db.commit()
