"""End-to-end workflow test — simulates a realistic user journey through the API.

An SDET thinks in workflows, not isolated endpoints. Quality means the full
sequence works: create → read → update → delete → confirm gone.
A single green unit test on delete_todo() does not prove the HTTP layer,
serialization, and persistence all work together across a release.

This test chains multiple API calls the way a client or integration test harness would.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_full_todo_lifecycle():
  # Workflow: create → read → update → read → delete → confirm gone
  #
  # Quality risk: any break in the chain blocks real user tasks. Progressive release
  # depends on this workflow passing before wider rollout.
    # Step 1: Create
    create_response = client.post(
        "/todos",
        json={
            "title": "Prepare quarterly report",
            "description": "Q1 deliverable",
        },
    )
    assert create_response.status_code == 201
    todo = create_response.json()
    todo_id = todo["id"]
    assert todo["title"] == "Prepare quarterly report"
    assert todo["completed"] is False

    # Step 2: Read — confirm persistence after create
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Q1 deliverable"

    # Step 3: Update — mark complete and rename
    update_response = client.put(
        f"/todos/{todo_id}",
        json={
            "title": "Prepare quarterly report (done)",
            "completed": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["completed"] is True

    # Step 4: Read — confirm update persisted
    verify_response = client.get(f"/todos/{todo_id}")
    assert verify_response.status_code == 200
    assert verify_response.json()["title"] == "Prepare quarterly report (done)"

    # Step 5: Delete
    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 204

    # Step 6: Confirm item no longer exists
    final_get = client.get(f"/todos/{todo_id}")
    assert final_get.status_code == 404, (
        "Workflow failed at final step: item still exists after delete. "
        "This is the intentional bug documented in BUG_REPORT.md."
    )

    # Step 7: Confirm list no longer includes the item
    list_response = client.get("/todos")
    assert list_response.status_code == 200
    ids = [item["id"] for item in list_response.json()]
    assert todo_id not in ids
