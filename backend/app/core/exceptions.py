from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class DuplicateSKUError(Exception):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"SKU '{sku}' already exists")


class DuplicateEmailError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email '{email}' already exists")


class DuplicateCustomerCodeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Customer code '{code}' already exists")


class InsufficientStockError(Exception):
    def __init__(self, available: int, requested: int):
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock. Available: {available}, Requested: {requested}"
        )


class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, resource_id: str):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} with id '{resource_id}' not found")


class ProductInUseError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' cannot be deleted — it has existing orders")


class CustomerInUseError(Exception):
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        super().__init__(f"Customer '{customer_id}' cannot be deleted — it has existing orders")


def register_exception_handlers(app):
    @app.exception_handler(DuplicateSKUError)
    async def duplicate_sku_handler(request: Request, exc: DuplicateSKUError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(DuplicateEmailError)
    async def duplicate_email_handler(request: Request, exc: DuplicateEmailError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(DuplicateCustomerCodeError)
    async def duplicate_code_handler(request: Request, exc: DuplicateCustomerCodeError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(ProductInUseError)
    async def product_in_use_handler(request: Request, exc: ProductInUseError):
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(CustomerInUseError)
    async def customer_in_use_handler(request: Request, exc: CustomerInUseError):
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": str(exc)}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail}
        )
