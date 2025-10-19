from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


@pytest.mark.asyncio
async def test_user_crud_flow(client: "SimpleAsyncClient") -> None:
    """Validate user CRUD endpoints end-to-end using the async client.

    Args:
        client: Async client fixture for interacting with the API.
    """
    owner_payload = {"name": "Owner", "email": "owner@example.com", "password": "secret123"}
    signup_response = await client.post("/auth/signup", json=owner_payload)
    assert signup_response.status_code == 201

    login_response = await client.post(
        "/auth/login", json={"email": owner_payload["email"], "password": owner_payload["password"]}
    )
    assert login_response.status_code == 200
    owner_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {owner_token}"}

    new_user_payload = {"name": "Second", "email": "second@example.com", "password": "anothersecret"}
    create_response = await client.post("/users", json=new_user_payload, headers=headers)
    assert create_response.status_code == 201
    created_user = create_response.json()
    created_user_id = created_user["id"]
    assert created_user["email"] == new_user_payload["email"]

    list_response = await client.get("/users", headers=headers)
    assert list_response.status_code == 200
    users = list_response.json()
    assert any(user["email"] == new_user_payload["email"] for user in users)

    detail_response = await client.get(f"/users/{created_user_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == new_user_payload["name"]

    update_payload = {"name": "Updated Second", "password": "newpass456"}
    update_response = await client.put(f"/users/{created_user_id}", json=update_payload, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_payload["name"]

    delete_response = await client.delete(f"/users/{created_user_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/users/{created_user_id}", headers=headers)
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_resources(client: "SimpleAsyncClient") -> None:
    """Ensure refresh tokens cannot be used for resource access or refresh swaps."""

    payload = {"name": "Owner", "email": "owner@example.com", "password": "secret123"}
    signup_response = await client.post("/auth/signup", json=payload)
    assert signup_response.status_code == 201

    login_response = await client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    refresh_headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    protected_response = await client.get("/users", headers=refresh_headers)
    assert protected_response.status_code == 401

    wrong_refresh_response = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert wrong_refresh_response.status_code == 401
