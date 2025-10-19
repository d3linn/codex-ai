from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


@pytest.mark.asyncio
async def test_user_crud_flow(client: "SimpleAsyncClient") -> None:
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
