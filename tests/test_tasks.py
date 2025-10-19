from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


async def _create_user_and_get_token(
    client: "SimpleAsyncClient", name: str, email: str, password: str
) -> str:
    """Register a user and return a fresh access token.

    Args:
        client: Async client used to call the API.
        name: Name for the new user.
        email: Email for the new user.
        password: Password for the new user.

    Returns:
        str: Access token issued for the created user.
    """
    signup_payload = {"name": name, "email": email, "password": password}
    signup_response = await client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == 201

    login_response = await client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_task_crud_and_permissions(client: "SimpleAsyncClient") -> None:
    """Ensure task endpoints enforce ownership and support full CRUD operations.

    Args:
        client: Async client fixture for interacting with the API.
    """
    owner_token = await _create_user_and_get_token(client, "Owner", "owner@example.com", "secret123")
    other_token = await _create_user_and_get_token(client, "Other", "other@example.com", "secret456")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    task_payload = {"title": "Task 1", "description": "First task", "completed": False}
    create_response = await client.post("/tasks", json=task_payload, headers=owner_headers)
    assert create_response.status_code == 201
    created_task = create_response.json()
    task_id = created_task["id"]
    assert created_task["title"] == task_payload["title"]

    list_response = await client.get("/tasks", headers=owner_headers)
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id

    detail_response = await client.get(f"/tasks/{task_id}", headers=owner_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == task_payload["description"]

    forbidden_update = await client.put(
        f"/tasks/{task_id}", json={"title": "Hacked", "completed": True}, headers=other_headers
    )
    assert forbidden_update.status_code == 403

    update_payload = {"title": "Updated Task", "description": "Updated", "completed": True}
    update_response = await client.put(f"/tasks/{task_id}", json=update_payload, headers=owner_headers)
    assert update_response.status_code == 200
    assert update_response.json()["completed"] is True

    forbidden_delete = await client.delete(f"/tasks/{task_id}", headers=other_headers)
    assert forbidden_delete.status_code == 403

    delete_response = await client.delete(f"/tasks/{task_id}", headers=owner_headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/tasks/{task_id}", headers=owner_headers)
    assert missing_response.status_code == 404
