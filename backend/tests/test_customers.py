import pytest
from httpx import AsyncClient

CUSTOMER_PAYLOAD = {
    "customer_code": "CUST-001",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "phone": "+1-555-0100",
}


async def create_customer(client: AsyncClient, payload: dict = None) -> dict:
    payload = payload or CUSTOMER_PAYLOAD
    return await client.post("/customers/", json=payload)


class TestCreateCustomer:
    async def test_create_customer_success(self, client: AsyncClient):
        resp = await create_customer(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["email"] == "alice@example.com"
        assert data["customer_code"] == "CUST-001"
        assert "id" in data

    async def test_create_customer_code_normalised_to_uppercase(self, client: AsyncClient):
        payload = {**CUSTOMER_PAYLOAD, "customer_code": "cust-lower"}
        resp = await create_customer(client, payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["customer_code"] == "CUST-LOWER"

    async def test_create_customer_duplicate_email(self, client: AsyncClient):
        await create_customer(client)
        payload = {**CUSTOMER_PAYLOAD, "customer_code": "CUST-002"}
        resp = await create_customer(client, payload)
        assert resp.status_code == 400
        assert resp.json()["success"] is False
        assert "already exists" in resp.json()["message"]

    async def test_create_customer_duplicate_code(self, client: AsyncClient):
        await create_customer(client)
        payload = {**CUSTOMER_PAYLOAD, "email": "other@example.com"}
        resp = await create_customer(client, payload)
        assert resp.status_code == 400
        assert resp.json()["success"] is False
        assert "already exists" in resp.json()["message"]

    async def test_create_customer_invalid_email(self, client: AsyncClient):
        payload = {**CUSTOMER_PAYLOAD, "email": "not-an-email", "customer_code": "CUST-BAD"}
        resp = await create_customer(client, payload)
        assert resp.status_code == 422


class TestListCustomers:
    async def test_list_customers_empty(self, client: AsyncClient):
        resp = await client.get("/customers/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_list_customers_returns_created(self, client: AsyncClient):
        await create_customer(client)
        resp = await client.get("/customers/")
        assert len(resp.json()["data"]) == 1


class TestGetCustomer:
    async def test_get_customer_by_id(self, client: AsyncClient):
        created = (await create_customer(client)).json()["data"]
        resp = await client.get(f"/customers/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created["id"]

    async def test_get_customer_not_found(self, client: AsyncClient):
        resp = await client.get("/customers/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateCustomer:
    async def test_update_customer_name(self, client: AsyncClient):
        created = (await create_customer(client)).json()["data"]
        resp = await client.put(
            f"/customers/{created['id']}", json={"name": "Alice Johnson"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Alice Johnson"

    async def test_update_customer_email_duplicate(self, client: AsyncClient):
        c1 = (await create_customer(client)).json()["data"]
        await create_customer(
            client, {**CUSTOMER_PAYLOAD, "customer_code": "CUST-002", "email": "bob@example.com"}
        )
        resp = await client.put(
            f"/customers/{c1['id']}", json={"email": "bob@example.com"}
        )
        assert resp.status_code == 400

    async def test_update_customer_not_found(self, client: AsyncClient):
        resp = await client.put("/customers/nonexistent-id", json={"name": "Ghost"})
        assert resp.status_code == 404


class TestDeleteCustomer:
    async def test_delete_customer(self, client: AsyncClient):
        created = (await create_customer(client)).json()["data"]
        resp = await client.delete(f"/customers/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        get_resp = await client.get(f"/customers/{created['id']}")
        assert get_resp.status_code == 404

    async def test_delete_customer_not_found(self, client: AsyncClient):
        resp = await client.delete("/customers/nonexistent-id")
        assert resp.status_code == 404
