from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.customer import Customer
from app.models.order import Order
from app.models.products import Product
from app.schemas.order import OrderCreate
from app.core.exceptions import InsufficientStockError, ResourceNotFoundError


async def get_all_orders(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Order]:
    result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_order_by_id(db: AsyncSession, order_id: str) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise ResourceNotFoundError("Order", order_id)
    return order


async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    # Step 1: validate customer exists
    customer = await db.execute(
        select(Customer).where(Customer.id == data.customer_id)
    )
    if not customer.scalar_one_or_none():
        raise ResourceNotFoundError("Customer", data.customer_id)

    # Step 2 & 3: validate product exists (quantity > 0 is enforced by the schema)
    product_result = await db.execute(
        select(Product).where(Product.id == data.product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise ResourceNotFoundError("Product", data.product_id)

    # Step 4: validate inventory availability
    if product.stock < data.quantity:
        raise InsufficientStockError(product.stock, data.quantity)

    # Step 5: calculate total price
    total_price = float(product.price) * data.quantity

    # Step 6: reduce stock
    product.stock -= data.quantity
    db.add(product)

    # Step 7: create order
    order = Order(
        customer_id=data.customer_id,
        product_id=data.product_id,
        quantity=data.quantity,
        total_price=total_price,
    )
    db.add(order)

    # Step 8: commit atomically
    await db.commit()
    await db.refresh(order)
    return order
