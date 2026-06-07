# Inventory Management System (IMS) — Backend

A production-ready REST API for managing products, customers, and orders, built with FastAPI, PostgreSQL, and async SQLAlchemy.

---

## Architecture

```
app/
├── api/            # Thin routers — HTTP in, service call, HTTP out
│   ├── products.py
│   ├── customers.py
│   └── orders.py
├── core/
│   ├── config.py   # Pydantic settings (env-driven)
│   └── exceptions.py  # Custom exceptions + unified error handlers
├── db/
│   ├── base.py     # SQLAlchemy DeclarativeBase
│   └── database.py # Async engine + session factory
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response models
│   └── response.py # Generic APIResponse[T] wrapper
├── services/       # Business logic layer
└── main.py         # App factory, lifespan, router registration
```

---

## API Endpoints

### Products

| Method | Path | Description |
|--------|------|-------------|
| GET | `/products/` | List all products (paginated) |
| POST | `/products/` | Create a product |
| GET | `/products/{id}` | Get a product by ID |
| PUT | `/products/{id}` | Update a product |
| DELETE | `/products/{id}` | Delete a product |

### Customers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/customers/` | List all customers (paginated) |
| POST | `/customers/` | Create a customer |
| GET | `/customers/{id}` | Get a customer by ID |
| PUT | `/customers/{id}` | Update a customer |
| DELETE | `/customers/{id}` | Delete a customer |

### Orders

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orders/` | List all orders (paginated) |
| POST | `/orders/` | Create an order (deducts stock atomically) |
| GET | `/orders/{id}` | Get an order by ID |

---

## Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "message": "Insufficient stock. Available: 5, Requested: 10"
}
```

---

## Local Setup

### Prerequisites
- Python 3.9+
- PostgreSQL running locally

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env            # then edit DATABASE_URL

# 4. Run the server
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

---

## Docker Setup

```bash
# Build and start both api + postgres
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down

# Stop and delete volume (fresh DB)
docker-compose down -v
```

API is available at http://localhost:8000

---

## Running Tests

Tests use an in-memory SQLite database — no PostgreSQL required.

```bash
# Install test deps (already in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific module
pytest tests/test_orders.py -v
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async SQLAlchemy DB URL | `postgresql+asyncpg://user:pass@localhost:5432/ims_db` |
| `APP_NAME` | Application name shown in docs | `Inventory Management API` |
| `DEBUG` | Enables SQLAlchemy echo | `False` |

---

## Sample Requests

**Create a product:**
```bash
curl -X POST http://localhost:8000/products/ \
  -H "Content-Type: application/json" \
  -d '{"sku": "WIDGET-01", "name": "Blue Widget", "price": 9.99, "stock": 50}'
```

**Create an order:**
```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "<uuid>", "product_id": "<uuid>", "quantity": 3}'
```

**Sample order response:**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "customer_id": "e5f6g7h8-...",
    "product_id": "i9j0k1l2-...",
    "quantity": 3,
    "total_price": 29.97,
    "created_at": "2026-06-07T11:00:00Z"
  }
}
```

---

## Verification Checklist

- [x] Product CRUD (GET list, GET by ID, POST, PUT, DELETE)
- [x] Customer CRUD (GET list, GET by ID, POST, PUT, DELETE)
- [x] Order creation with 8-step validation flow
- [x] Atomic inventory reduction on order creation
- [x] Insufficient stock protection (400 with clear message)
- [x] Unique SKU, email, and customer code enforcement
- [x] Foreign key constraints (Order → Customer, Order → Product)
- [x] Swagger / OpenAPI documentation at `/docs`
- [x] PostgreSQL persistence via async SQLAlchemy
- [x] Docker + Docker Compose support
- [x] Automated test suite (pytest + aiosqlite, no external DB needed)
- [x] Consistent `{"success", "data"}` response envelope
- [x] Service layer with thin routers
