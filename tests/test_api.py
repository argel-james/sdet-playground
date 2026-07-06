"""API / integration tests — endpoints tested as an external client would call them.

Unlike unit tests, these verify the full HTTP stack:
  routing → request parsing → service call → status code → response body

This is closer to how a web client, mobile app, or CI smoke job
would interact with the API. A green unit test does not guarantee
the endpoint is wired correctly.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
  # Verifies: service is reachable for deployment smoke tests.
  # Quality risk: a broken deploy ships to users before anyone notices.
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_todo_returns_201_with_expected_fields():
  # Verifies: POST /todos returns 201 and the contract fields clients depend on.
  # Quality risk: clients cannot parse responses or persist new item IDs.
    response = client.post(
        "/todos",
        json={"title": "Verify budget numbers", "description": "Q1 planning"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Verify budget numbers"
    assert body["description"] == "Q1 planning"
    assert body["completed"] is False
    assert "id" in body


def test_create_todo_missing_title_returns_422():
  # Verifies: requests without a title are rejected at the API boundary.
  # Quality risk: invalid payloads enter the system or cause 500 errors in production.
    response = client.post("/todos", json={"description": "no title provided"})

    assert response.status_code == 422


def test_create_todo_whitespace_title_returns_422():
  # Verifies: whitespace-only titles are rejected via Pydantic validation.
  # Quality risk: empty-named records pollute todo lists and break UI sorting.
    response = client.post("/todos", json={"title": "   "})

    assert response.status_code == 422


def test_create_duplicate_todo_returns_409():
  # Verifies: duplicate titles return 409 Conflict with a clear HTTP signal.
  # Quality risk: integrators cannot distinguish a duplicate from a server error.
    client.post("/todos", json={"title": "Sync cloud project"})
    response = client.post("/todos", json={"title": "Sync cloud project"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_get_todo_returns_200():
  # Verifies: a known ID returns the stored todo.
  # Quality risk: read-after-create fails, breaking trust in persistence.
    create_response = client.post("/todos", json={"title": "Load dependencies"})
    todo_id = create_response.json()["id"]

    response = client.get(f"/todos/{todo_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Load dependencies"


def test_get_todo_not_found_returns_404():
  # Verifies: unknown IDs return 404, not 500 or empty 200.
  # Quality risk: clients cannot tell "missing" from "exists but empty".
    response = client.get("/todos/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_list_todos_returns_all_items():
  # Verifies: GET /todos returns every stored item.
  # Quality risk: list view omits items, causing incomplete dashboards.
    client.post("/todos", json={"title": "Task A"})
    client.post("/todos", json={"title": "Task B"})

    response = client.get("/todos")

    assert response.status_code == 200
    titles = {item["title"] for item in response.json()}
    assert titles == {"Task A", "Task B"}


def test_update_todo_returns_200():
  # Verifies: PUT updates fields and returns the new state.
  # Quality risk: save operations appear to succeed but changes are lost.
    create_response = client.post("/todos", json={"title": "Draft revision"})
    todo_id = create_response.json()["id"]

    response = client.put(
        f"/todos/{todo_id}",
        json={"title": "Final revision", "completed": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Final revision"
    assert body["completed"] is True


def test_update_todo_not_found_returns_404():
  # Verifies: updating a missing todo returns 404.
  # Quality risk: clients get ambiguous errors when syncing stale local state.
    response = client.put(
        "/todos/00000000-0000-0000-0000-000000000000",
        json={"title": "Ghost task"},
    )

    assert response.status_code == 404


def test_update_todo_duplicate_title_returns_409():
  # Verifies: renaming to an existing title is blocked at the API layer.
  # Quality risk: two items share one name; delete/update targets the wrong record.
    first = client.post("/todos", json={"title": "Alpha task"}).json()
    second = client.post("/todos", json={"title": "Beta task"}).json()

    response = client.put(
        f"/todos/{second['id']}",
        json={"title": "Alpha task"},
    )

    assert response.status_code == 409


def test_delete_todo_returns_204():
  # Verifies: DELETE returns the expected success status code.
  # Quality risk: clients cannot tell if delete was accepted vs rejected.
    create_response = client.post("/todos", json={"title": "Temporary markup"})
    todo_id = create_response.json()["id"]

    response = client.delete(f"/todos/{todo_id}")

    assert response.status_code == 204


def test_delete_todo_not_found_returns_404():
  # Verifies: deleting a missing todo returns 404.
  # Quality risk: double-delete or stale-ID deletes appear as server errors.
    response = client.delete("/todos/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_delete_returns_204_but_item_still_exists():
  # Verifies: after DELETE, the item must not be retrievable.
  # Quality risk: HTTP 204 looks correct but state is wrong — a silent regression
  # that only behavioral assertions catch (status-code-only tests would pass).
    create_response = client.post("/todos", json={"title": "Stale item ref"})
    todo_id = create_response.json()["id"]

    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404, (
        "Delete returned 204 but item still exists — see BUG_REPORT.md"
    )
