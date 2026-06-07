from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.products import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.exceptions import (
    DuplicateSKUError,
    ProductInUseError,
    ResourceNotFoundError,
)


async def get_all_products(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Product]:
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_product_by_id(db: AsyncSession, product_id: str) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise ResourceNotFoundError("Product", product_id)
    return product


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    existing = await db.execute(select(Product).where(Product.sku == data.sku))
    if existing.scalar_one_or_none():
        raise DuplicateSKUError(data.sku)

    product = Product(
        sku=data.sku,
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, product_id: str, data: ProductUpdate
) -> Product:
    product = await get_product_by_id(db, product_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)

    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: str) -> None:
    product = await get_product_by_id(db, product_id)

    # Guard against deleting products that have orders (FK RESTRICT enforced here too)
    from app.models.order import Order
    has_orders = await db.execute(
        select(Order.id).where(Order.product_id == product_id).limit(1)
    )
    if has_orders.scalar_one_or_none():
        raise ProductInUseError(product_id)

    await db.delete(product)
    await db.commit()
