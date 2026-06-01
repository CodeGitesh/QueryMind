"""
Integration tests for the FastAPI endpoints.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_schema_list_endpoint(client):
    response = await client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "schemas" in data
    schema_names = [s["name"] for s in data["schemas"]]
    assert "ecommerce" in schema_names
    assert "hr" in schema_names
    assert "finance" in schema_names


@pytest.mark.asyncio
async def test_query_validation_too_long(client):
    """Query longer than 500 chars should be rejected by Pydantic."""
    response = await client.post(
        "/api/query",
        json={"query": "A" * 501, "schema_name": "ecommerce"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_invalid_schema(client):
    """Unknown schema name should be rejected."""
    response = await client.post(
        "/api/query",
        json={"query": "Show all customers", "schema_name": "invalid_schema"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_endpoint(client):
    response = await client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_history_pagination(client):
    response = await client.get("/api/history?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


@pytest.mark.asyncio
async def test_delete_nonexistent_history(client):
    response = await client.delete("/api/history/nonexistent-id-12345")
    assert response.status_code == 404
