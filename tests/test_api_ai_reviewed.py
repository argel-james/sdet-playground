"""API negative tests: AI-suggested, human-reviewed.

An SDET does not blindly commit AI-generated tests. Each suggestion is checked
against acceptance criteria (TEST_PLAN.md), realistic client behavior, and
project scope before landing in the suite.

Full review log (kept / rejected / rationale): AI_TESTING_REVIEW.md
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_todo_title_too_long_returns_422():
    # AI suggestion: reject titles over the schema max length.
    # Review: KEPT — real validation gap; clients may send oversized strings from forms.
    # Quality risk: unbounded input breaks DB columns and UI layout in production APIs.
    long_title = "x" * 101

    response = client.post("/todos", json={"title": long_title})

    assert response.status_code == 422


def test_create_todo_empty_json_body_returns_422():
    # AI suggestion: POST with empty body should fail validation.
    # Review: KEPT — common integrator mistake; must not return 500.
    # Quality risk: server errors on bad input erode API trust and flood error logs.
    response = client.post("/todos", json={})

    assert response.status_code == 422


def test_create_todo_title_wrong_type_returns_422():
    # AI suggestion: title sent as integer should be rejected.
    # Review: KEPT — type safety at the API boundary; plugins may serialize badly.
    # Quality risk: wrong types slip into service layer and cause runtime exceptions.
    response = client.post("/todos", json={"title": 12345})

    assert response.status_code == 422


def test_update_todo_whitespace_title_returns_422():
    # AI suggestion: PUT with whitespace-only title should fail like POST does.
    # Review: KEPT — symmetric validation; rename-to-blank is a realistic user error.
    # Quality risk: blank titles after rename corrupt list views and search indexes.
    created = client.post("/todos", json={"title": "Valid title"}).json()

    response = client.put(
        f"/todos/{created['id']}",
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_create_todo_null_title_returns_422():
    # AI suggestion: explicit null title should be rejected.
    # Review: KEPT — JSON null is different from missing field; both must fail safely.
    # Quality risk: null values bypass business rules if validation is incomplete.
    response = client.post("/todos", json={"title": None})

    assert response.status_code == 422
