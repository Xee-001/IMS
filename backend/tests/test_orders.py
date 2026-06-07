import pytest
from httpx import AsyncClient

PRODUCT_PAYLOAD = {"sku": "PROD-001", "name": "Test Product", "price": 25.00, "stock": 10}
CUSTOMER_PAYLOAD = {
    "customer_code": "CUST-001",
    "name": "Bob Buyer",
    "email": "bob@example.com",
    "phone": "+1-555-0200",
}


async def setup_product_and_customer(client: AsyncClient) -> tuple:
    product = (await client.post("/products/", json=PRODUCT_PAYLOAD)).json()["data"]
    customer = (await client.post("/customers/", json=CUSTOMER_PAYLOAD)).json()["data"]
    return product, customer


class TestCreateOrder:
    async def test_create_order_success(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 3},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["quantity"] == 3
        assert data["total_price"] == 75.0
        assert data["customer_id"] == customer["id"]
        assert data["product_id"] == product["id"]

    async def test_create_order_reduces_stock(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 4},
        )
        # Verify stock was reduced from 10 to 6
        updated = (await client.get(f"/products/{product['id']}")).json()["data"]
        assert updated["stock"] == 6

    async def test_create_order_insufficient_stock(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 999},
        )
        assert resp.status_code == 400
        assert resp.json()["success"] is False
        assert "Insufficient" in resp.json()["message"]

    async def test_create_order_missing_customer(self, client: AsyncClient):
        product, _ = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": "nonexistent-customer", "product_id": product["id"], "quantity": 1},
        )
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    async def test_create_order_missing_product(self, client: AsyncClient):
        _, customer = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": "nonexistent-product", "quantity": 1},
        )
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    async def test_create_order_zero_quantity_rejected(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 0},
        )
        assert resp.status_code == 422

    async def test_create_order_negative_quantity_rejected(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        resp = await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": -5},
        )
        assert resp.status_code == 422

    async def test_stock_not_reduced_on_failure(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 999},
        )
        # Stock should remain unchanged after a failed order
        unchanged = (await client.get(f"/products/{product['id']}")).json()["data"]
        assert unchanged["stock"] == 10


class TestListOrders:
    async def test_list_orders_empty(self, client: AsyncClient):
        resp = await client.get("/orders/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_list_orders_returns_created(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        await client.post(
            "/orders/",
            json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 1},
        )
        resp = await client.get("/orders/")
        assert len(resp.json()["data"]) == 1


class TestGetOrder:
    async def test_get_order_by_id(self, client: AsyncClient):
        product, customer = await setup_product_and_customer(client)
        created = (
            await client.post(
                "/orders/",
                json={"customer_id": customer["id"], "product_id": product["id"], "quantity": 2},
            )
        ).json()["data"]
        resp = await client.get(f"/orders/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created["id"]

    async def test_get_order_not_found(self, client: AsyncClient):
        resp = await client.get("/orders/nonexistent-id")
        assert resp.status_code == 404
