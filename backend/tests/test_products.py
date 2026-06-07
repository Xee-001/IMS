import pytest
from httpx import AsyncClient

PRODUCT_PAYLOAD = {
    "sku": "WIDGET-001",
    "name": "Blue Widget",
    "description": "A sturdy blue widget",
    "price": 19.99,
    "stock": 100,
}


async def create_product(client: AsyncClient, payload: dict = None) -> dict:
    payload = payload or PRODUCT_PAYLOAD
    resp = await client.post("/products/", json=payload)
    return resp


class TestCreateProduct:
    async def test_create_product_success(self, client: AsyncClient):
        resp = await create_product(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["sku"] == "WIDGET-001"
        assert data["name"] == "Blue Widget"
        assert data["price"] == 19.99
        assert data["stock"] == 100
        assert "id" in data

    async def test_create_product_sku_normalised_to_uppercase(self, client: AsyncClient):
        payload = {**PRODUCT_PAYLOAD, "sku": "widget-lowercase"}
        resp = await create_product(client, payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["sku"] == "WIDGET-LOWERCASE"

    async def test_create_product_duplicate_sku(self, client: AsyncClient):
        await create_product(client)
        resp = await create_product(client)  # same SKU
        assert resp.status_code == 400
        assert resp.json()["success"] is False
        assert "already exists" in resp.json()["message"]

    async def test_create_product_invalid_price(self, client: AsyncClient):
        payload = {**PRODUCT_PAYLOAD, "price": -5.0, "sku": "PRICE-BAD"}
        resp = await create_product(client, payload)
        assert resp.status_code == 422

    async def test_create_product_zero_price(self, client: AsyncClient):
        payload = {**PRODUCT_PAYLOAD, "price": 0, "sku": "PRICE-ZERO"}
        resp = await create_product(client, payload)
        assert resp.status_code == 422

    async def test_create_product_negative_stock(self, client: AsyncClient):
        payload = {**PRODUCT_PAYLOAD, "stock": -1, "sku": "STOCK-BAD"}
        resp = await create_product(client, payload)
        assert resp.status_code == 422


class TestListProducts:
    async def test_list_products_empty(self, client: AsyncClient):
        resp = await client.get("/products/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []

    async def test_list_products_returns_created(self, client: AsyncClient):
        await create_product(client)
        resp = await client.get("/products/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    async def test_list_products_pagination(self, client: AsyncClient):
        for i in range(5):
            await create_product(client, {**PRODUCT_PAYLOAD, "sku": f"P-{i:03d}"})
        resp = await client.get("/products/?skip=2&limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2


class TestGetProduct:
    async def test_get_product_by_id(self, client: AsyncClient):
        created = (await create_product(client)).json()["data"]
        resp = await client.get(f"/products/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created["id"]

    async def test_get_product_not_found(self, client: AsyncClient):
        resp = await client.get("/products/nonexistent-id")
        assert resp.status_code == 404
        assert resp.json()["success"] is False


class TestUpdateProduct:
    async def test_update_product(self, client: AsyncClient):
        created = (await create_product(client)).json()["data"]
        resp = await client.put(
            f"/products/{created['id']}", json={"price": 29.99, "stock": 50}
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["price"] == 29.99
        assert data["stock"] == 50
        assert data["sku"] == created["sku"]  # SKU unchanged

    async def test_update_product_not_found(self, client: AsyncClient):
        resp = await client.put("/products/nonexistent-id", json={"price": 9.99})
        assert resp.status_code == 404


class TestDeleteProduct:
    async def test_delete_product(self, client: AsyncClient):
        created = (await create_product(client)).json()["data"]
        resp = await client.delete(f"/products/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # Confirm gone
        get_resp = await client.get(f"/products/{created['id']}")
        assert get_resp.status_code == 404

    async def test_delete_product_not_found(self, client: AsyncClient):
        resp = await client.delete("/products/nonexistent-id")
        assert resp.status_code == 404
