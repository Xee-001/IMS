# 📦 Inventory Management System (IMS)

A full-stack web application to manage **products**, **customers**, and **orders** — with automatic inventory tracking built in.

> **Reading this for the first time?**  
> Start from the top and follow each section in order. Every concept is explained simply before the commands are given.

---

## Table of Contents

1. [What Does This App Do?](#1-what-does-this-app-do)
2. [High Level Design (HLD)](#2-high-level-design-hld)
3. [Tech Stack — What We Use and Why](#3-tech-stack--what-we-use-and-why)
4. [Project Structure](#4-project-structure)
5. [How Everything Connects (Data Flow)](#5-how-everything-connects-data-flow)
6. [Local Setup — Step by Step](#6-local-setup--step-by-step)
7. [Running with Docker](#7-running-with-docker)
8. [API Reference](#8-api-reference)
9. [Running Tests](#9-running-tests)
10. [Deployment Guide](#10-deployment-guide)
11. [Submission Checklist](#11-submission-checklist)

---

## 1. What Does This App Do?

Imagine you run a small warehouse. You need to:

- **Track products** — what items you sell, at what price, how many are left in stock
- **Track customers** — who is buying from you
- **Place orders** — when a customer buys something, stock must go down automatically

This app does exactly that, with a web UI and a REST API.

**Key rules enforced by the system:**
- Every product has a unique SKU (like a barcode — no two products share one)
- Every customer has a unique email and unique customer code
- You cannot order more units than are in stock
- When an order is placed, stock reduces instantly and automatically

---

## 2. High Level Design (HLD)

### Big Picture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                       │
│            Opens http://localhost:5173                      │
└─────────────────────┬───────────────────────────────────────┘
                      │  clicks buttons, fills forms
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   REACT FRONTEND                            │
│         (Vite + React + React Router + Axios)               │
│                                                             │
│   Pages: Dashboard | Products | Customers | Orders          │
│   Services: productService.js | customerService.js | ...    │
└─────────────────────┬───────────────────────────────────────┘
                      │  HTTP requests (GET, POST, PUT, DELETE)
                      │  e.g. POST /orders/  →  {"customer_id":...}
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                           │
│              (Python + FastAPI + Uvicorn)                   │
│                                                             │
│  Routers  →  Services  →  SQLAlchemy ORM  →  PostgreSQL     │
│                                                             │
│  api/products.py    →  services/product_service.py          │
│  api/customers.py   →  services/customer_service.py         │
│  api/orders.py      →  services/order_service.py            │
└─────────────────────┬───────────────────────────────────────┘
                      │  SQL queries (async)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                       │
│                                                             │
│  Tables: products | customers | orders                      │
│  Relationships: orders.customer_id → customers.id           │
│                 orders.product_id  → products.id            │
└─────────────────────────────────────────────────────────────┘
```

### Database Design

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   products   │       │    orders    │       │  customers   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ id (PK)      │   ┌──►│ id (PK)      │
│ sku (UNIQUE) │   └───│ product_id   │   │   │ customer_code│
│ name         │       │ customer_id  │───┘   │ name         │
│ description  │       │ quantity     │       │ email(UNIQUE)│
│ price        │       │ total_price  │       │ phone        │
│ stock        │       │ created_at   │       └──────────────┘
└──────────────┘       └──────────────┘
```

### Order Creation Flow (8 Steps)

```
POST /orders/  →  1. Does customer exist?       NO  → 404
                  2. Does product exist?        NO  → 404
                  3. quantity > 0?              NO  → 422
                  4. product.stock >= quantity? NO  → 400 "Insufficient stock"
                  5. Calculate total_price = price × quantity
                  6. Reduce product.stock by quantity
                  7. Create Order record
                  8. Commit both changes atomically (all or nothing)
                                                    → 201 Created
```

**"Atomically"** means: if step 7 fails, step 6 is also undone. The database never ends up in a half-updated state.

### Request/Response Format

Every API response looks like this:

```json
// Success
{ "success": true,  "data": { ... } }

// Error
{ "success": false, "message": "Insufficient stock. Available: 3, Requested: 10" }
```

---

## 3. Tech Stack — What We Use and Why

| Layer | Technology | Why We Chose It |
|---|---|---|
| **Frontend** | React 18 | Most popular UI library; component-based makes code reusable |
| **Frontend build** | Vite | Much faster than Create React App; modern tooling |
| **Frontend routing** | React Router v6 | Standard for multi-page React apps |
| **Frontend HTTP** | Axios | Cleaner API than the built-in `fetch`; auto JSON parsing |
| **Backend** | FastAPI (Python) | Very fast; auto-generates Swagger docs; async support |
| **Database** | PostgreSQL | Industry-standard relational DB; enforces data integrity |
| **ORM** | SQLAlchemy 2 (Async) | Lets us write Python instead of raw SQL; type-safe |
| **Validation** | Pydantic v2 | Validates all incoming data automatically |
| **Containerization** | Docker + Compose | "Works on my machine" → works everywhere |
| **Testing** | pytest + pytest-asyncio | Standard Python testing; async-aware |
| **Test DB** | SQLite (in-memory) | Tests run without needing a real PostgreSQL server |

---

## 4. Project Structure

```
IMS/
├── backend/                    ← Python API
│   ├── app/
│   │   ├── api/                ← HTTP route handlers (thin)
│   │   │   ├── products.py
│   │   │   ├── customers.py
│   │   │   └── orders.py
│   │   ├── core/
│   │   │   ├── config.py       ← reads .env variables
│   │   │   └── exceptions.py   ← custom error classes + handlers
│   │   ├── db/
│   │   │   ├── base.py         ← SQLAlchemy base class
│   │   │   └── database.py     ← DB engine + session
│   │   ├── models/             ← SQLAlchemy table definitions
│   │   │   ├── products.py
│   │   │   ├── customer.py
│   │   │   └── order.py
│   │   ├── schemas/            ← Pydantic input/output shapes
│   │   │   ├── product.py
│   │   │   ├── customer.py
│   │   │   ├── order.py
│   │   │   └── response.py     ← APIResponse[T] wrapper
│   │   ├── services/           ← Business logic lives here
│   │   │   ├── product_service.py
│   │   │   ├── customer_service.py
│   │   │   └── order_service.py
│   │   └── main.py             ← App entry point
│   ├── tests/
│   │   ├── conftest.py         ← shared fixtures
│   │   ├── test_products.py
│   │   ├── test_customers.py
│   │   └── test_orders.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── pytest.ini
│
└── frontend/                   ← React UI
    ├── src/
    │   ├── api/
    │   │   └── axios.js        ← configured axios instance
    │   ├── services/           ← one file per resource (mirrors backend)
    │   │   ├── productService.js
    │   │   ├── customerService.js
    │   │   └── orderService.js
    │   ├── components/         ← reusable UI pieces
    │   │   ├── Navbar.jsx
    │   │   ├── Modal.jsx
    │   │   ├── Alert.jsx
    │   │   └── Spinner.jsx
    │   ├── pages/              ← one file per screen
    │   │   ├── Dashboard.jsx
    │   │   ├── Products.jsx
    │   │   ├── Customers.jsx
    │   │   └── Orders.jsx
    │   ├── App.jsx             ← router wiring
    │   ├── main.jsx            ← React entry point
    │   └── index.css           ← all styles
    ├── .env                    ← VITE_API_URL=http://localhost:8000
    └── package.json
```

---

## 5. How Everything Connects (Data Flow)

Here is what happens when a user places an order from the UI:

```
Step 1: User opens Orders page
  → frontend calls GET /customers/ and GET /products/
  → dropdowns populate with real data from the database

Step 2: User selects customer, product, quantity → clicks "Place Order"
  → frontend calls POST /orders/ with { customer_id, product_id, quantity }

Step 3: Backend router (api/orders.py) receives the request
  → calls order_service.create_order(db, data)

Step 4: order_service runs the validation steps
  → customer exists? product exists? enough stock?
  → calculates total_price = price × quantity
  → deducts stock from product
  → inserts new Order row
  → commits both changes in one transaction

Step 5: Backend returns { "success": true, "data": { order } }

Step 6: Frontend shows a green "Order placed successfully" alert
  → reloads the orders list
  → the product's stock count in the Products page is now lower
```

---

## 6. Local Setup — Step by Step

### What you need installed first

| Tool | How to check | Install |
|---|---|---|
| Python 3.9+ | `python3 --version` | python.org |
| Node.js 18+ | `node --version` | nodejs.org |
| PostgreSQL | `psql --version` | postgresql.org |
| Git | `git --version` | git-scm.com |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ims.git
cd ims
```

---

### Step 2 — Set up the Backend

```bash
# Move into the backend folder
cd backend

# Create a virtual environment
# (a virtual environment isolates Python packages so they don't clash with system packages)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate         # Mac/Linux
# venv\Scripts\activate          # Windows

# Install all Python packages
pip install -r requirements.txt
```

**Create the `.env` file** (backend reads config from here):

```bash
# Create the file
cp .env.example .env    # if .env.example exists, or just create it manually
```

Edit `.env` to match your PostgreSQL setup:

```env
DATABASE_URL=postgresql+asyncpg://YOUR_PG_USER:YOUR_PG_PASSWORD@localhost:5432/ims_db
APP_NAME=Inventory Management API
DEBUG=True
```

> **What is `postgresql+asyncpg://`?**  
> This is the connection string. It tells SQLAlchemy to use PostgreSQL via the `asyncpg` driver.  
> Format: `postgresql+asyncpg://username:password@host:port/database_name`

**Create the database** in PostgreSQL:

```bash
psql -U postgres
CREATE DATABASE ims_db;
\q
```

**Start the backend server:**

```bash
uvicorn app.main:app --reload
```

> `--reload` means the server automatically restarts when you save a file. Good for development.

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Open http://localhost:8000/docs to see the auto-generated Swagger API documentation.

---

### Step 3 — Set up the Frontend

Open a **new terminal** (keep the backend running in the first one):

```bash
# From the project root
cd frontend

# Install all JavaScript packages
npm install

# Start the development server
npm run dev
```

You should see:
```
  VITE  Local:   http://localhost:5173/
```

Open http://localhost:5173 in your browser. The UI is now live.

> The frontend reads `VITE_API_URL` from the `.env` file in the frontend folder.  
> By default it points to `http://localhost:8000` (the backend).

---

### Step 4 — Try it out

1. Go to **Products** → Add a product (e.g. SKU: `WIDGET-01`, Price: `9.99`, Stock: `50`)
2. Go to **Customers** → Add a customer
3. Go to **Orders** → Place an order for that product
4. Go back to **Products** → the stock count has gone down!

---

## 7. Running with Docker

Docker packages the app into containers so you don't need to install Python, PostgreSQL, or worry about OS differences.

### What is Docker? (Beginner Explanation)

Think of a Docker container like a shipping container — it has everything the app needs inside (Python, packages, config). You can send it anywhere and it works the same.

`docker-compose.yml` defines TWO containers that work together:
- `api` — runs the FastAPI backend
- `db` — runs PostgreSQL

They talk to each other over a private network Docker creates automatically.

### Running it

```bash
# Make sure Docker Desktop is running first

cd backend

# Build the image and start both containers
docker-compose up --build

# The first time this runs, it:
# 1. Downloads python:3.9-slim and postgres:15-alpine images
# 2. Installs all Python packages inside the container
# 3. Starts PostgreSQL (waits until it's healthy)
# 4. Starts the FastAPI server
```

After it starts:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

**Stop everything:**
```bash
docker-compose down          # stops containers
docker-compose down -v       # stops AND deletes the database volume (fresh start)
```

### What the Dockerfile does (explained line by line)

```dockerfile
FROM python:3.9-slim          # start from an official Python image
WORKDIR /app                  # all commands run from /app inside the container
COPY requirements.txt .       # copy requirements first (for layer caching)
RUN pip install -r requirements.txt   # install packages
COPY . .                      # copy the rest of the code
EXPOSE 8000                   # document that port 8000 is used
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **Layer caching explained:**  
> Docker builds images in layers. If `requirements.txt` hasn't changed, Docker reuses the cached `pip install` layer and rebuilds are much faster (seconds instead of minutes).

---

## 8. API Reference

All endpoints return `{ "success": true/false, "data": ... }`.

### Products

```
GET    /products/            List all products (supports ?skip=0&limit=100)
POST   /products/            Create a product
GET    /products/{id}        Get one product
PUT    /products/{id}        Update a product (SKU cannot be changed)
DELETE /products/{id}        Delete a product (fails if it has orders)
```

**Create a product:**
```bash
curl -X POST http://localhost:8000/products/ \
  -H "Content-Type: application/json" \
  -d '{"sku": "WIDGET-01", "name": "Blue Widget", "price": 9.99, "stock": 50}'
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "abc123...",
    "sku": "WIDGET-01",
    "name": "Blue Widget",
    "price": 9.99,
    "stock": 50,
    "description": null
  }
}
```

### Customers

```
GET    /customers/           List all customers
POST   /customers/           Create a customer
GET    /customers/{id}       Get one customer
PUT    /customers/{id}       Update a customer (code cannot be changed)
DELETE /customers/{id}       Delete a customer (fails if it has orders)
```

**Create a customer:**
```bash
curl -X POST http://localhost:8000/customers/ \
  -H "Content-Type: application/json" \
  -d '{"customer_code": "CUST-001", "name": "Alice", "email": "alice@example.com", "phone": "+1-555-0100"}'
```

### Orders

```
GET    /orders/              List all orders (most recent first)
POST   /orders/              Place an order (reduces stock automatically)
GET    /orders/{id}          Get one order
```

**Place an order:**
```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "<uuid>", "product_id": "<uuid>", "quantity": 3}'
```

**Insufficient stock error:**
```json
{
  "success": false,
  "message": "Insufficient stock. Available: 2, Requested: 3"
}
```

### Health Check Endpoints

```
GET  /        →  {"message": "Inventory Management API Running"}
GET  /health  →  {"status": "healthy"}
GET  /docs    →  Swagger UI (interactive API explorer)
```

---

## 9. Running Tests

The test suite has 41 tests covering every endpoint, every validation rule, and every failure case.

**Tests run against an in-memory SQLite database — no PostgreSQL needed.**

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output (shows each test name)
pytest -v

# Run just the order tests
pytest tests/test_orders.py -v

# Run a specific test
pytest tests/test_orders.py::TestCreateOrder::test_create_order_insufficient_stock -v
```

Expected output:
```
41 passed in 0.25s
```

### What is tested?

| Module | Tests |
|---|---|
| Products | Create, duplicate SKU, invalid price, invalid stock, list, get by ID, update, delete |
| Customers | Create, duplicate email, duplicate code, invalid email, list, get by ID, update, delete |
| Orders | Create, stock reduction verified, insufficient stock, missing customer, missing product, zero quantity, negative quantity, stock unchanged on failure, list, get by ID |

---

## 10. Deployment Guide

This is the priority order for submitting the assignment:

---

### Priority 1 — Push to GitHub

> **Why first?** Everything else links back to your GitHub repo.

```bash
# From the IMS root folder
git init
git add .
git commit -m "Initial commit: IMS full-stack application"

# Create a new repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/ims.git
git branch -M main
git push -u origin main
```

---

### Priority 2 — Push Backend Image to Docker Hub

> Docker Hub is like GitHub, but for Docker container images.

**Step 1: Create a free account at hub.docker.com**

**Step 2: Build and tag the image:**
```bash
cd backend
docker build -t YOUR_DOCKERHUB_USERNAME/ims-backend:latest .
```

**Step 3: Log in and push:**
```bash
docker login
docker push YOUR_DOCKERHUB_USERNAME/ims-backend:latest
```

Your image link will be: `docker.io/YOUR_USERNAME/ims-backend:latest`

---

### Priority 3 — Deploy Backend to Railway

> **Railway** is a free hosting platform for backend apps and databases.

1. Go to **railway.app** and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo** → select your `ims` repo
3. Select the `/backend` directory
4. Railway auto-detects the Dockerfile and builds it
5. Add environment variables (click **Variables**):
   ```
   DATABASE_URL   = postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
   APP_NAME       = Inventory Management API
   DEBUG          = False
   ```
   Railway auto-provisions a PostgreSQL database — click **New** → **Database** → **PostgreSQL** and Railway fills in `DATABASE_URL` for you.
6. Click **Deploy** — in 2 minutes your backend is live at `https://ims-backend.up.railway.app`

> **Alternative:** Render.com works identically. Free tier available.

---

### Priority 4 — Deploy Frontend to Vercel

> **Vercel** is a free platform specifically designed for React/Vite frontends.

1. Go to **vercel.com** and sign in with GitHub
2. Click **Add New Project** → import your `ims` repo
3. Set **Root Directory** to `frontend`
4. Vercel auto-detects Vite
5. Add environment variable:
   ```
   VITE_API_URL = https://YOUR_BACKEND_URL.up.railway.app
   ```
6. Click **Deploy** — your frontend is live at `https://ims.vercel.app`

> **Important:** The `VITE_API_URL` must point to your deployed backend, NOT localhost.

---

### Priority 5 — Enable CORS on Backend

When the frontend is deployed on Vercel and calls the backend on Railway, the browser enforces **CORS** (Cross-Origin Resource Sharing). You need to tell the backend "yes, requests from Vercel are allowed."

Add this to `backend/app/main.py` **before** the routers:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # local dev
        "https://YOUR_APP.vercel.app",    # deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> **What is CORS?**  
> When your browser loads a page from `ims.vercel.app` and that page tries to call `ims-backend.railway.app`, the browser first asks the backend "do you allow this?" If the backend doesn't say yes (via the CORS header), the browser blocks the request. This middleware makes the backend say yes.

---

### Summary — What to put in the form

| Field | Value |
|---|---|
| GitHub Repository Link | `https://github.com/YOUR_USERNAME/ims` |
| Backend Docker Hub Image Link | `https://hub.docker.com/r/YOUR_USERNAME/ims-backend` |
| Frontend Hosted URL | `https://ims.vercel.app` |
| Backend API Hosted URL | `https://ims-backend.up.railway.app` |

---

## 11. Submission Checklist

Go through each item before submitting:

**Backend**
- [x] `GET /products/` — list all products
- [x] `POST /products/` — create with SKU uniqueness, price > 0, stock >= 0
- [x] `GET /products/{id}` — get one product
- [x] `PUT /products/{id}` — update product
- [x] `DELETE /products/{id}` — delete product
- [x] `GET /customers/` — list all customers
- [x] `POST /customers/` — create with unique email and customer code
- [x] `GET /customers/{id}` — get one customer
- [x] `PUT /customers/{id}` — update customer
- [x] `DELETE /customers/{id}` — delete customer
- [x] `GET /orders/` — list all orders
- [x] `POST /orders/` — 8-step validation, atomic stock reduction
- [x] `GET /orders/{id}` — get one order
- [x] Swagger UI at `/docs`
- [x] All responses use `{"success": bool, "data"/"message": ...}` format
- [x] Service layer — business logic NOT in routers
- [x] Proper FK relationships in database
- [x] 41 automated tests, all passing
- [x] Docker + Docker Compose

**Frontend**
- [x] Dashboard with live stats
- [x] Products page — list, create, edit, delete
- [x] Customers page — list, create, edit, delete
- [x] Orders page — list, place order with stock preview
- [x] Low stock warning (products with ≤ 5 units highlighted)
- [x] Error messages from API displayed to user
- [x] Responsive design (works on mobile)

**Deployment (to do)**
- [ ] Code on GitHub (public repo)
- [ ] Docker image on Docker Hub
- [ ] Backend deployed (Railway / Render)
- [ ] CORS configured for deployed frontend URL
- [ ] Frontend deployed (Vercel / Netlify)
- [ ] All 4 URLs tested and working
