# Inventory Management System (IMS) - Code Structure Analysis

**Date:** June 6, 2024  
**Framework:** FastAPI + SQLAlchemy (Async) + PostgreSQL  
**Status:** Early Stage - Development

---

## 1. PROJECT OVERVIEW

### Purpose
An Inventory Management System backend API for managing:
- **Products** - SKU, pricing, stock levels
- **Customers** - Customer information and tracking
- **Orders** - Order creation with inventory management

### Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (async driver: asyncpg)
- **ORM:** SQLAlchemy 2.0 with async support
- **Validation:** Pydantic v2
- **ASGI Server:** Uvicorn

### Current Features
✅ Product management (CRUD)  
✅ Customer management (CRUD)  
⚠️ Order management (Partially implemented - issues detected)  
✅ Database connection pooling (async)  
✅ Health check endpoints

---

## 2. CODE STRUCTURE & ARCHITECTURE

```
/app
├── main.py                          # FastAPI app entry point
├── core/
│   └── config.py                    # Configuration & settings management
├── db/
│   ├── database.py                  # Database connection & session factory
│   └── base.py                      # SQLAlchemy declarative base
├── models/                          # Database ORM models
│   ├── customer.py                  # Customer entity
│   ├── products.py                  # Product entity
│   └── order.py                     # Order entity
├── schemas/                         # Pydantic validation schemas
│   ├── customer.py                  # Customer request/response schemas
│   ├── product.py                   # Product request/response schemas
│   └── order.py                     # Order request/response schemas
├── api/                             # API routers/endpoints
│   ├── customers.py                 # Customer endpoints
│   ├── products.py                  # Product endpoints
│   └── orders.py                    # Order endpoints (NEEDS FIX)
└── services/                        # Business logic layer (UNUSED - empty files)
    ├── customer_service.py
    ├── product_service.py
    └── order_service.py
```

### Architecture Pattern
**Current:** Direct API → Model → Database (No service layer)  
**Recommended:** API → Service Layer → Repository → Model → Database

---

## 3. DETAILED COMPONENT BREAKDOWN

### 3.1 Models Layer

#### Customer Model
```
✅ UUID-based primary key
✅ Unique constraints on customer_code & email
✅ Required fields: code, name, email, phone
- Missing: address, city, country, tax_id (business info)
- Missing: created_at, updated_at timestamps
```

#### Product Model
```
✅ UUID-based primary key
✅ Unique constraint on SKU
✅ Stock management with default value
✅ Price stored as Numeric(10,2) for accuracy
- Missing: category, supplier_id
- Missing: created_at, updated_at timestamps
- Missing: reorder_level threshold
```

#### Order Model
```
⚠️ UUID-based primary key
⚠️ Basic order structure (customer_id, product_id, quantity, total_price)
❌ MISSING: Foreign key constraints
❌ MISSING: Order status field (pending/processing/completed/cancelled)
❌ MISSING: Payment status
⚠️ created_at field exists but missing in response schema
- Missing: delivery_date, shipping_address
- Missing: notes/comments
```

### 3.2 Schemas (Validation Layer)

#### Consistency Issues Found
- `OrderResponse` schema missing `created_at` field (exists in model)
- `OrderCreate` doesn't validate quantity > 0
- No pagination schemas defined
- No error response schemas

### 3.3 API Routes

#### Products API (`/products`)
```
GET  /products          ✅ List all products (with response model)
POST /products          ✅ Create product (SKU uniqueness check)
- MISSING: GET /products/{id} - fetch single product
- MISSING: PUT /products/{id} - update product
- MISSING: DELETE /products/{id} - delete product
```

#### Customers API (`/customers`)
```
GET  /customers         ✅ List all customers (with response model)
POST /customers         ✅ Create customer (code & email uniqueness)
- MISSING: GET /customers/{id} - fetch single customer
- MISSING: PUT /customers/{id} - update customer
- MISSING: DELETE /customers/{id} - delete customer
```

#### Orders API (`/orders`) - **CRITICAL ISSUES**
```
❌ GET  /orders         Returns dummy message, NOT actual orders
   - Should fetch all orders from database with filters
   - Should include pagination
   
❌ POST /orders         Stock reduction NOT persisted to DB
   - Product stock is reduced in memory but not saved
   - Missing transaction safety - can lead to data loss
   - Missing order validation (negative quantities, zero quantities)
   
- MISSING: GET /orders/{id} - fetch single order
- MISSING: PUT /orders/{id} - update order status
- MISSING: DELETE /orders/{id} - cancel order (with stock restoration)
- MISSING: Filtering by customer_id, status, date range
```

---

## 4. CRITICAL ISSUES IDENTIFIED

### Issue 1: GET /orders Returns Dummy Message
**Severity:** 🔴 HIGH  
**Location:** `app/api/orders.py:22-26`  
**Problem:**
```python
@router.get("/")
async def get_orders():
    return {"message": "Orders endpoint working"}  # ❌ No DB query!
```
**Impact:** Cannot retrieve orders from database. Endpoint is non-functional.

**Fix:** Should query database and return list of orders
```python
@router.get("/", response_model=List[OrderResponse])
async def get_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    orders = result.scalars().all()
    return orders
```

---

### Issue 2: POST /orders Stock Update Not Persisted
**Severity:** 🔴 CRITICAL  
**Location:** `app/api/orders.py:80-92`  
**Problem:**
```python
product.stock -= order.quantity  # ❌ Modified in memory only

new_order = Order(
    customer_id=order.customer_id,
    product_id=order.product_id,
    quantity=order.quantity,
    total_price=total_price
)

db.add(new_order)
await db.commit()  # ❌ Only commits the order, NOT the product changes!
```

**Impact:** 
- Product stock is reduced in memory but rolled back on commit
- Multiple orders can exceed available stock
- Inventory becomes inconsistent with orders
- Data integrity violation

**Fix:** Must explicitly add product to session before commit
```python
product.stock -= order.quantity
db.add(product)  # ✅ Add product to session

new_order = Order(...)
db.add(new_order)
await db.commit()  # ✅ Now commits both
```

---

### Issue 3: Missing Foreign Key Constraints
**Severity:** 🟠 MEDIUM  
**Location:** `app/models/order.py`  
**Problem:** Order table references `customer_id` and `product_id` but no FK constraints

**Impact:** Orphaned orders possible, referential integrity issues

**Fix:** Add ForeignKey constraints with ondelete cascade
```python
customer_id: Mapped[str] = mapped_column(
    String,
    ForeignKey("customers.id", ondelete="CASCADE"),
    nullable=False
)
```

---

### Issue 4: OrderResponse Missing created_at
**Severity:** 🟡 MEDIUM  
**Location:** `app/schemas/order.py`  
**Problem:** Order model has `created_at` but schema doesn't expose it

**Fix:** Add field to OrderResponse schema
```python
class OrderResponse(BaseModel):
    id: str
    customer_id: str
    product_id: str
    quantity: int
    total_price: float
    created_at: datetime  # ✅ Add this
```

---

### Issue 5: No Order Status Tracking
**Severity:** 🟡 MEDIUM  
**Location:** `app/models/order.py`  
**Problem:** Orders don't have status (pending/processing/completed/cancelled)

**Impact:** Cannot track order lifecycle or handle cancellations

---

## 5. HIGH-LEVEL DESIGN (HLD)

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT / FRONTEND                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Routes (Endpoints)                              │   │
│  │  ├─ /products (GET, POST)                            │   │
│  │  ├─ /customers (GET, POST)                           │   │
│  │  ├─ /orders (GET, POST) ← ISSUES HERE              │   │
│  │  └─ /health, /db-test                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Pydantic Schema Validation Layer                    │   │
│  │  ├─ ProductCreate, ProductResponse                  │   │
│  │  ├─ CustomerCreate, CustomerResponse                │   │
│  │  ├─ OrderCreate, OrderResponse                      │   │
│  └──────────────────────▼──────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Business Logic (Currently INLINE in routes)        │   │
│  │  ├─ Stock validation & reduction                    │   │
│  │  ├─ Duplicate checking                              │   │
│  │  ├─ Order calculations                              │   │
│  └──────────────────────▼──────────────────────────────┘   │
│                         │ SQLAlchemy ORM                      │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  SQLAlchemy Models (ORM)                             │   │
│  │  ├─ Product (products table)                        │   │
│  │  ├─ Customer (customers table)                      │   │
│  │  ├─ Order (orders table)                            │   │
│  └──────────────────────▼──────────────────────────────┘   │
│                         │ asyncpg driver                      │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  AsyncSessionLocal Connection Pool                  │   │
│  └──────────────────────▼──────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ Connection String (DATABASE_URL)
┌────────────────────────▼────────────────────────────────────┐
│                  PostgreSQL Database                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tables:                                              │   │
│  │ ├─ products (id, sku, name, price, stock)          │   │
│  │ ├─ customers (id, code, name, email, phone)        │   │
│  │ ├─ orders (id, customer_id, product_id,qty, price) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow for Order Creation (Current - With Bug)

```
Client POST /orders
        │
        ▼
┌─────────────────────────────────┐
│ OrderCreate Validation (Pydantic)│
└────────────┬────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Check Customer Exists            │
│ SELECT FROM customers WHERE id   │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Check Product Exists             │
│ SELECT FROM products WHERE id    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Validate Stock                   │
│ Check if stock >= quantity       │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Reduce Stock (IN MEMORY)         │ ← BUG: Not committed!
│ product.stock -= quantity        │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Create Order Object              │
│ new_order = Order(...)           │
│ db.add(new_order)                │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ COMMIT Transaction               │
│ await db.commit()                │ ← Only commits order, product changes lost!
└────────────┬─────────────────────┘
             │
             ▼
Response OrderResponse (Created)
```

---

## 6. RECOMMENDED IMPROVEMENTS

### Priority 1: Fix Critical Bugs

#### 1.1 Fix GET /orders - Return Actual Orders
```python
@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .offset(skip)
        .limit(limit)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()
```

#### 1.2 Fix POST /orders - Persist Stock Changes
```python
# Change this:
product.stock -= order.quantity
new_order = Order(...)
db.add(new_order)
await db.commit()

# To this:
product.stock -= order.quantity
db.add(product)  # ← Add this line!
new_order = Order(...)
db.add(new_order)
await db.commit()
```

#### 1.3 Fix OrderResponse Schema
```python
from datetime import datetime

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    product_id: str
    quantity: int
    total_price: float
    created_at: datetime  # ← Add this
    
    class Config:
        from_attributes = True  # Pydantic v2 replaces orm_mode
```

### Priority 2: Add Missing Functionality

#### 2.1 Add Foreign Key Constraints
```python
# In Order model
customer_id: Mapped[str] = mapped_column(
    String,
    ForeignKey("customers.id", ondelete="CASCADE"),
    nullable=False
)
product_id: Mapped[str] = mapped_column(
    String,
    ForeignKey("products.id", ondelete="RESTRICT"),
    nullable=False
)
```

#### 2.2 Add Order Status Field
```python
# In Order model
from sqlalchemy import Enum
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

status: Mapped[OrderStatus] = mapped_column(
    Enum(OrderStatus),
    default=OrderStatus.PENDING,
    nullable=False
)
```

#### 2.3 Add Input Validation
```python
from pydantic import Field

class OrderCreate(BaseModel):
    customer_id: str
    product_id: str
    quantity: int = Field(gt=0, description="Must be greater than 0")
```

#### 2.4 Add GET by ID Endpoints
```python
@router.get("/{id}", response_model=OrderResponse)
async def get_order_by_id(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
```

### Priority 3: Refactor Code Structure

#### 3.1 Implement Service Layer Pattern
```
api/orders.py (Routes - 20 lines)
    ↓
services/order_service.py (Business Logic - 50 lines)
    ↓
models/order.py (Database Layer)
```

#### 3.2 Create Repository Pattern
```python
# app/repositories/order_repository.py
class OrderRepository:
    async def create(self, db, order_data) -> Order
    async def get_by_id(self, db, id) -> Order
    async def list_all(self, db, skip, limit) -> List[Order]
    async def update_status(self, db, id, status) -> Order
```

#### 3.3 Add Error Handling
```python
from app.core.exceptions import NotFoundError, InsufficientStockError

class OrderService:
    async def create_order(self, db, order_data):
        if not self.product_exists(id):
            raise NotFoundError("Product not found")
        if product.stock < quantity:
            raise InsufficientStockError("Not enough stock")
```

### Priority 4: Add Missing Features

#### 4.1 Order Filtering & Search
```python
@router.get("/")
async def list_orders(
    customer_id: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Order)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    if status:
        query = query.where(Order.status == status)
    # ... more filters
```

#### 4.2 Order Cancellation with Stock Restoration
```python
@router.put("/{id}/cancel", response_model=OrderResponse)
async def cancel_order(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    order = await get_order_by_id_or_404(db, id)
    
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    # Restore stock
    product = await db.get(Product, order.product_id)
    product.stock += order.quantity
    
    order.status = OrderStatus.CANCELLED
    await db.commit()
    return order
```

#### 4.3 Add Timestamps to Models
```python
from datetime import datetime

class BaseModel(Base):
    __abstract__ = True
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
```

### Priority 5: Testing & Quality

#### 5.1 Add Unit Tests
```python
# tests/test_orders.py
async def test_create_order_reduces_stock():
    # Arrange: Create product with 10 stock
    # Act: Create order for 3 units
    # Assert: Stock reduced to 7
    
async def test_insufficient_stock_raises_error():
    # Arrange: Create product with 5 stock
    # Act: Try to create order for 10 units
    # Assert: HTTPException raised with 400
```

#### 5.2 Add Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Order created: {order.id} for customer {order.customer_id}")
logger.warning(f"Low stock alert: Product {product_id} has only {product.stock} units")
```

#### 5.3 Add Request/Response Examples
```python
class OrderCreate(BaseModel):
    customer_id: str
    product_id: str
    quantity: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": "550e8400-e29b-41d4-a716-446655440000",
                "product_id": "550e8400-e29b-41d4-a716-446655440001",
                "quantity": 5
            }
        }
    }
```

---

## 7. COMPARISON: Current vs. Improved Code

### GET /orders Endpoint

**CURRENT (❌ Broken):**
```python
@router.get("/")
async def get_orders():
    return {"message": "Orders endpoint working"}
```

**IMPROVED (✅ Fixed):**
```python
@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Order)
    
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    if status:
        query = query.where(Order.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()
```

### POST /orders Endpoint

**CURRENT (❌ Stock not saved):**
```python
product.stock -= order.quantity  # Memory only

new_order = Order(...)
db.add(new_order)
await db.commit()  # Only commits order!
```

**IMPROVED (✅ Stock persisted):**
```python
product.stock -= order.quantity
db.add(product)  # ← ADD THIS LINE

new_order = Order(...)
db.add(new_order)
await db.commit()  # Commits both now!
```

---

## 8. SUMMARY TABLE: Issues & Fixes

| Issue | Severity | Type | Location | Fix |
|-------|----------|------|----------|-----|
| GET returns dummy message | 🔴 HIGH | Functional | orders.py:22 | Query database |
| Stock not persisted | 🔴 CRITICAL | Data Loss | orders.py:80 | Add `db.add(product)` |
| Missing created_at in schema | 🟡 MEDIUM | Schema | order.py schema | Add field |
| No FK constraints | 🟡 MEDIUM | Integrity | order.py model | Add ForeignKey |
| No order status tracking | 🟡 MEDIUM | Feature | order.py model | Add status enum |
| No input validation | 🟡 MEDIUM | Validation | schemas | Use Field constraints |
| No service layer | 🟢 LOW | Architecture | all | Create service layer |
| No pagination | 🟢 LOW | Feature | api routes | Add skip/limit params |
| No error responses defined | 🟢 LOW | Documentation | - | Add error schemas |
| Unused services folder | 🟢 LOW | Code Organization | services/ | Implement services |

---

## 9. NEXT STEPS (Recommended Order)

1. **Immediate (Critical):**
   - Fix POST /orders stock persistence bug
   - Fix GET /orders to return actual orders
   - Update OrderResponse schema with created_at

2. **Short-term (High Priority):**
   - Add foreign key constraints
   - Add order status field
   - Add input validation

3. **Medium-term:**
   - Implement service layer
   - Add filtering & search
   - Add order cancellation logic

4. **Long-term:**
   - Add tests (unit & integration)
   - Add comprehensive logging
   - Add API documentation with Swagger examples
   - Performance optimization (indexes, query optimization)

---

## 10. ENDPOINTS REFERENCE

### Current State
```
GET  / → Home
GET  /health → Health check
GET  /db-test → DB connection test
GET  /products → List products ✅
POST /products → Create product ✅
GET  /customers → List customers ✅
POST /customers → Create customer ✅
GET  /orders → Dummy message ❌
POST /orders → Buggy stock update ❌
```

### Recommended (After Fixes)
```
GET  /products → List (with pagination)
POST /products → Create
GET  /products/{id} → Retrieve
PUT  /products/{id} → Update
DELETE /products/{id} → Delete

GET  /customers → List (with pagination)
POST /customers → Create
GET  /customers/{id} → Retrieve
PUT  /customers/{id} → Update
DELETE /customers/{id} → Delete

GET  /orders → List (with filters & pagination) ← FIX
POST /orders → Create (with stock persistence) ← FIX
GET  /orders/{id} → Retrieve
PUT  /orders/{id}/cancel → Cancel & restore stock
PUT  /orders/{id}/status → Update status
```

---

**Document Version:** 1.0  
**Last Updated:** June 6, 2024
