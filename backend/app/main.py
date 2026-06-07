from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.base import Base
from app.db.database import engine
from app.models import Customer, Order, Product  # noqa: F401 — ensures models are registered

from app.api.customers import router as customer_router
from app.api.orders import router as order_router
from app.api.products import router as product_router
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Inventory Management API",
    description="A production-ready IMS built with FastAPI, PostgreSQL, and SQLAlchemy.",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

# Allow the React frontend (local dev + any deployed Vercel URL) to call this API.
# In production, replace "*" with your exact frontend domain for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://ims-tau-nine.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_router)
app.include_router(customer_router)
app.include_router(order_router)


@app.get("/", tags=["Health"])
def home():
    return {"message": "Inventory Management API Running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.get("/db-test", tags=["Health"])
async def db_test():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
    return {"database": "connected", "result": result.scalar()}
