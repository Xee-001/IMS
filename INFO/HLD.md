# HIGH-LEVEL DESIGN (HLD) - Inventory Management System

## 1. System Overview

### Purpose
The Inventory Management System (IMS) is a RESTful backend API designed to manage:
- **Product Catalog** - SKU management, pricing, inventory levels
- **Customer Registry** - Customer information with unique identifiers
- **Order Processing** - Order creation, fulfillment, and inventory tracking

### Architecture Type
**Layered Architecture** with potential for **Microservices** in future

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                      │
│         (REST API - Endpoints via FastAPI)              │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                 Validation Layer                         │
│           (Pydantic Schema Validation)                  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│               Business Logic Layer                       │
│        (Services - Order processing, Stock mgmt)        │
│               [CURRENTLY MISSING]                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Repository Layer                           │
│        (Database access patterns)                       │
│               [CURRENTLY MISSING]                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Data Access Layer                          │
│         (SQLAlchemy ORM - Models)                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Persistence Layer                          │
│          (PostgreSQL Database)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Core Components

#### API Layer (FastAPI Routers)
```
/api/products.py
├── GET /products → List all products
├── POST /products → Create new product
├── GET /products/{id} → Get product details
├── PUT /products/{id} → Update product
└── DELETE /products/{id} → Delete product

/api/customers.py
├── GET /customers → List all customers
├── POST /customers → Create new customer
├── GET /customers/{id} → Get customer details
├── PUT /customers/{id} → Update customer
└── DELETE /customers/{id} → Delete customer

/api/orders.py
├── GET /orders → List orders (with filters)
├── POST /orders → Create order (with inventory mgmt)
├── GET /orders/{id} → Get order details
├── PUT /orders/{id}/status → Update order status
└── DELETE /orders/{id}/cancel → Cancel order (restore stock)
```

#### Data Models (SQLAlchemy ORM)
```
Product
├── id (UUID) - Primary Key
├── sku (String, Unique)
├── name (String)
├── description (Text)
├── price (Numeric)
├── stock (Integer)
└── Relationships: Orders

Customer
├── id (UUID) - Primary Key
├── customer_code (String, Unique)
├── name (String)
├── email (String, Unique)
├── phone (String)
└── Relationships: Orders

Order
├── id (UUID) - Primary Key
├── customer_id (FK) - Foreign Key to Customer
├── product_id (FK) - Foreign Key to Product
├── quantity (Integer)
├── total_price (Numeric)
├── status (Enum: pending, processing, completed, cancelled)
├── created_at (DateTime)
└── updated_at (DateTime)
```

#### Database Schema
```sql
CREATE TABLE products (
    id VARCHAR PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE customers (
    id VARCHAR PRIMARY KEY,
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE orders (
    id VARCHAR PRIMARY KEY,
    customer_id VARCHAR NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id VARCHAR NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    total_price NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

---

## 3. Key Workflows

### 3.1 Order Creation Workflow

```
┌─ START: Client sends POST /orders
│
├─ 1. VALIDATE REQUEST
│  ├─ Pydantic schema validation
│  ├─ Check quantity > 0
│  └─ Return 422 if invalid
│
├─ 2. VERIFY CUSTOMER
│  ├─ Query: SELECT * FROM customers WHERE id = ?
│  ├─ If not found → 404 error
│  └─ Continue if found
│
├─ 3. VERIFY PRODUCT
│  ├─ Query: SELECT * FROM products WHERE id = ?
│  ├─ If not found → 404 error
│  └─ Continue if found
│
├─ 4. CHECK STOCK AVAILABILITY
│  ├─ If product.stock < order.quantity → 400 error
│  └─ Continue if sufficient stock
│
├─ 5. CALCULATE ORDER TOTAL
│  └─ total_price = product.price × quantity
│
├─ 6. REDUCE INVENTORY
│  ├─ product.stock -= quantity
│  ├─ UPDATE products SET stock = ? WHERE id = ?
│  └─ Persist to DB
│
├─ 7. CREATE ORDER RECORD
│  ├─ INSERT INTO orders (...)
│  ├─ COMMIT TRANSACTION
│  └─ Retrieve created_at timestamp
│
└─ RETURN: 201 Created with OrderResponse
```

### 3.2 Stock Management Workflow

```
┌─ Order Creation
├─ Check available stock
├─ Reserve quantity
├─ Create order record
└─ Confirm inventory deduction

┌─ Order Cancellation
├─ Retrieve order details
├─ Check if already cancelled/completed
├─ Restore quantity: product.stock += order.quantity
├─ Update order status = 'cancelled'
└─ Commit changes

┌─ Low Stock Alert (Future)
├─ Query products WHERE stock < reorder_level
├─ Generate notification
└─ Flag for procurement
```

---

## 4. Data Flow Diagrams

### 4.1 System-level Data Flow

```
┌─────────────┐
│   Client    │ (Frontend/Mobile App)
└──────┬──────┘
       │ HTTP (REST)
       │
┌──────▼──────────────────────────────┐
│      FastAPI Application            │
│  ┌────────────────────────────────┐ │
│  │  API Routers (Products,         │ │
│  │   Customers, Orders)            │ │
│  └────────────┬───────────────────┘ │
│               │                     │
│  ┌────────────▼───────────────────┐ │
│  │  Pydantic Schemas               │ │
│  │  (Validation & Serialization)   │ │
│  └────────────┬───────────────────┘ │
│               │                     │
│  ┌────────────▼───────────────────┐ │
│  │  Business Logic (Inline)        │ │
│  │  • Stock validation             │ │
│  │  • Duplicate checking           │ │
│  │  • Calculations                 │ │
│  └────────────┬───────────────────┘ │
│               │                     │
│  ┌────────────▼───────────────────┐ │
│  │  SQLAlchemy ORM                 │ │
│  │  (Products, Customers, Orders)  │ │
│  └────────────┬───────────────────┘ │
└──────────────┼──────────────────────┘
               │ asyncpg driver
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL Database               │
│  ├─ products table                  │
│  ├─ customers table                 │
│  └─ orders table                    │
└─────────────────────────────────────┘
```

### 4.2 Order Submission Data Flow (Current - With Bug)

```
POST /orders {customer_id, product_id, quantity}
    │
    ▼
Validate Input (Pydantic)
    │
    ▼
SELECT customer ──→ ✓ Found
    │
    ▼
SELECT product ──→ ✓ Found
    │
    ▼
Check stock ──→ ✓ Sufficient (product.stock >= quantity)
    │
    ▼
Reduce stock: product.stock -= quantity  [IN MEMORY]
    │
    ▼
Create Order object
    │
    ▼
db.add(new_order)
    │
    ▼
db.commit() ──→ ❌ ONLY COMMITS ORDER!
                 ❌ PRODUCT STOCK CHANGE ROLLED BACK!
    │
    ▼
Return OrderResponse (201)
    │
    ▼
DATABASE STATE:
├─ orders table: NEW order inserted ✓
└─ products table: stock unchanged ✗ (BUG!)
```

### 4.3 Order Submission Data Flow (Fixed)

```
POST /orders {customer_id, product_id, quantity}
    │
    ▼
Validate Input (Pydantic)
    │
    ▼
SELECT customer ──→ ✓ Found
    │
    ▼
SELECT product ──→ ✓ Found
    │
    ▼
Check stock ──→ ✓ Sufficient
    │
    ▼
Reduce stock: product.stock -= quantity
    │
    ▼
db.add(product) ──→ ✓ MARK PRODUCT FOR UPDATE
    │
    ▼
Create Order object
    │
    ▼
db.add(new_order)
    │
    ▼
db.commit() ──→ ✓ COMMITS BOTH PRODUCT & ORDER
    │
    ▼
Return OrderResponse (201)
    │
    ▼
DATABASE STATE:
├─ orders table: NEW order inserted ✓
└─ products table: stock updated ✓ (FIXED!)
```

---

## 5. Technology Stack Justification

| Layer | Technology | Why? |
|-------|-----------|------|
| Framework | **FastAPI** | Modern, async-first, automatic OpenAPI docs, built-in validation |
| Async Driver | **asyncpg** | High-performance PostgreSQL async driver, concurrent handling |
| ORM | **SQLAlchemy 2.0** | Flexible, type-safe, excellent async support, industry standard |
| Database | **PostgreSQL** | ACID compliance, strong data integrity, JSON support |
| Validation | **Pydantic v2** | Schema validation, automatic serialization, type hints |
| Server | **Uvicorn** | ASGI server, performant, simple deployment |
| Connection Pool | **Built-in SQLAlchemy** | Handles concurrent requests efficiently |

---

## 6. Deployment Architecture

### 6.1 Production Deployment (Recommended)

```
┌────────────────────────────────────────────────────────┐
│                     Load Balancer                      │
│                   (Nginx/HAProxy)                      │
└────────────────────────┬───────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  Uvicorn     │ │  Uvicorn    │ │  Uvicorn    │
│  Worker 1    │ │  Worker 2   │ │  Worker 3   │
│  (FastAPI)   │ │  (FastAPI)  │ │  (FastAPI)  │
└───────┬──────┘ └──────┬──────┘ └──────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────┐          ┌──────────▼────────┐
│ Connection Pool  │          │ Redis Cache       │
│ (asyncpg)        │          │ (Optional future) │
└───────┬──────────┘          └───────────────────┘
        │
┌───────▼────────────────────────────────────────┐
│         PostgreSQL Database (Primary)          │
│  ├─ Transactions enabled                       │
│  ├─ Connection pooling: 20-50 connections     │
│  └─ Replication (optional)                     │
└────────────────────────────────────────────────┘
```

### 6.2 Horizontal Scaling

- **Stateless Design** - Each worker can handle any request
- **Connection Pooling** - Shared database connection pool across workers
- **Load Balancer** - Distributes requests across workers
- **Caching Layer** - Optional Redis for frequently accessed data

---

## 7. Security Considerations

### 7.1 Input Validation
✅ Pydantic schemas enforce data types  
⚠️ SQL injection: Parameterized queries prevent attacks  
⚠️ Missing: Rate limiting, API key auth, CORS configuration

### 7.2 Data Integrity
✅ Database transactions (ACID)  
✅ Foreign key constraints prevent orphaned records  
⚠️ Missing: Row-level security, audit logging

### 7.3 Future Security Enhancements
- [ ] Authentication (JWT)
- [ ] Authorization (Role-based access)
- [ ] Rate limiting
- [ ] API versioning
- [ ] Audit trails
- [ ] Encryption at rest

---

## 8. Performance Considerations

### 8.1 Current Optimizations
- ✅ Async/await for concurrent request handling
- ✅ Connection pooling (SQLAlchemy)
- ✅ Parameterized queries (SQL injection prevention)

### 8.2 Future Optimizations
- [ ] Database indexes (orders.customer_id, orders.product_id, orders.status)
- [ ] Query optimization (N+1 query prevention)
- [ ] Caching (Redis) for frequently accessed products
- [ ] Pagination for list endpoints
- [ ] Lazy loading for relationships

### 8.3 Database Indexes (Recommended)

```sql
-- Improve order queries
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Improve customer queries
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_code ON customers(customer_code);

-- Improve product queries
CREATE INDEX idx_products_sku ON products(sku);
```

---

## 9. Error Handling & Validation

### 9.1 Request Validation Levels

```
Level 1: Schema Validation (Pydantic)
├─ Type checking
├─ Required fields
└─ Format validation

Level 2: Business Logic Validation
├─ Customer exists
├─ Product exists
├─ Stock available
└─ Duplicate checking

Level 3: Database Constraints
├─ Primary key uniqueness
├─ Foreign key references
└─ NOT NULL constraints
```

### 9.2 Error Response Format

```json
{
    "detail": "Error message",
    "status_code": 400,
    "error_type": "ValidationError"
}
```

### 9.3 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET request fulfilled |
| 201 | Created | POST order created |
| 400 | Bad Request | Insufficient stock |
| 404 | Not Found | Customer not found |
| 422 | Validation Error | Invalid input format |
| 500 | Server Error | Database connection failed |

---

## 10. Scalability & Future Enhancements

### Phase 1 (Current)
- Basic CRUD operations
- Simple inventory management
- Single database

### Phase 2 (Recommended)
- Service layer implementation
- Order status tracking
- Comprehensive logging
- Unit & integration tests
- API documentation (Swagger)

### Phase 3 (Medium-term)
- Microservices (Products, Orders, Customers as separate services)
- Event-driven architecture (Order events)
- Caching layer (Redis)
- Message queue (RabbitMQ/Kafka) for async operations
- Search functionality (Elasticsearch)

### Phase 4 (Long-term)
- Distributed transactions (Saga pattern)
- Real-time notifications (WebSockets)
- Analytics & reporting
- Mobile app backend
- Third-party integrations

---

## 11. Risk Analysis

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| **Stock data loss** | HIGH | HIGH | Add `db.add(product)` in POST /orders |
| **Orphaned records** | MEDIUM | MEDIUM | Add foreign key constraints |
| **Race conditions** | MEDIUM | MEDIUM | Database locks, optimistic locking |
| **N+1 queries** | MEDIUM | MEDIUM | Query optimization, eager loading |
| **Database downtime** | HIGH | LOW | Replication, failover mechanism |
| **DDoS attacks** | MEDIUM | LOW | Rate limiting, WAF |

---

## 12. Monitoring & Observability (Future)

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Order created", extra={
    "order_id": order.id,
    "customer_id": order.customer_id,
    "quantity": order.quantity
})
```

### Metrics
- Request latency (p50, p95, p99)
- Database query time
- Order throughput (orders/sec)
- Stock accuracy
- Error rates

### Health Checks
```
GET /health → {status: "healthy"}
GET /db-test → {database: "connected"}
```

---

## 13. Architecture Decision Records (ADRs)

### ADR-1: Why Async?
- ✅ Multiple concurrent orders can be processed simultaneously
- ✅ Better resource utilization with asyncpg
- ✅ Non-blocking I/O for database operations

### ADR-2: Why PostgreSQL?
- ✅ ACID compliance for order transactions
- ✅ Strong data integrity with constraints
- ✅ Excellent for structured data

### ADR-3: Why Pydantic Schemas?
- ✅ Built-in validation (faster than manual checks)
- ✅ Automatic OpenAPI documentation
- ✅ Type safety

---

## Summary

The IMS is built on a **layered architecture** with **async FastAPI** handling requests, **Pydantic** validating data, **SQLAlchemy** managing database access, and **PostgreSQL** providing durable storage. 

**Current Status:** Functional but with critical bugs in order processing and missing features.

**Immediate Action:** Fix stock persistence in POST /orders endpoint.

**Long-term Vision:** Evolve into a microservices architecture with event-driven order processing, real-time inventory tracking, and comprehensive analytics.

---

**Document Version:** 1.0  
**Created:** June 6, 2024  
**Architecture Diagram Version:** Latest
