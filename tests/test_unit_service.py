"""Unit tests for app.service — business logic tested in isolation (no HTTP).

Unit tests answer: "Does this single function enforce the right rules?"
They run fast and pinpoint the exact layer where a defect lives.
"""

import pytest

from app.service import (
    DuplicateTitleError,
    EmptyTitleError,
    create_todo,
    delete_todo,
    get_todo,
    list_todos,
    update_todo,
)


def test_create_todo_success():
  # Verifies: a valid title creates a todo with expected default fields.
  # Quality risk: the core create path is broken, blocking all downstream workflows.
    todo = create_todo(title="Review project specs", description="Phase 1")

    assert todo["title"] == "Review project specs"
    assert todo["description"] == "Phase 1"
    assert todo["completed"] is False
    assert "id" in todo


def test_create_todo_strips_whitespace():
  # Verifies: leading/trailing whitespace is normalized before storage.
  # Quality risk: "Buy supplies" and "  Buy supplies  " could be treated as
  # different titles, bypassing duplicate detection or polluting search results.
    todo = create_todo(title="  Buy groceries  ")

    assert todo["title"] == "Buy groceries"


def test_create_todo_rejects_duplicate_title():
  # Verifies: duplicate titles are rejected at the service layer.
  # Quality risk: conflicting records break list views, filters, and sync workflows.
    create_todo(title="Archive project")

    with pytest.raises(DuplicateTitleError):
        create_todo(title="Archive project")


def test_create_todo_rejects_duplicate_title_case_insensitive():
  # Verifies: duplicate check is case-insensitive.
  # Quality risk: "Save File" and "save file" could coexist, causing user confusion
  # and inconsistent API behavior across clients.
    create_todo(title="Export PDF")

    with pytest.raises(DuplicateTitleError):
        create_todo(title="export pdf")


def test_create_todo_rejects_empty_title():
  # Verifies: blank titles cannot enter the store.
  # Quality risk: unnamed todos corrupt list UIs and make automation selectors unreliable.
    with pytest.raises(EmptyTitleError):
        create_todo(title="   ")


def test_get_todo_not_found():
  # Verifies: missing IDs return None instead of raising or returning garbage.
  # Quality risk: clients receive misleading data instead of a clear not-found signal.
    assert get_todo("nonexistent-id") is None


def test_update_todo_success():
  # Verifies: existing todos can be updated in place.
  # Quality risk: edits silently fail, causing data loss in multi-step workflows.
    created = create_todo(title="Check dimensions")
    updated = update_todo(created["id"], title="Check dimensions v2", completed=True)

    assert updated["title"] == "Check dimensions v2"
    assert updated["completed"] is True


def test_update_todo_rejects_duplicate_title():
  # Verifies: renaming a todo cannot collide with another todo's title.
  # Quality risk: two distinct items share one title, breaking update/delete targeting.
    first = create_todo(title="First audit")
    second = create_todo(title="Second audit")

    with pytest.raises(DuplicateTitleError):
        update_todo(second["id"], title="First audit")


def test_delete_todo_removes_item():
  # Verifies: delete actually removes the todo from the store.
  # Quality risk: "deleted" items still appear in lists — a classic regression
  # where the API returns success but state is wrong (see BUG_REPORT.md).
    created = create_todo(title="Remove obsolete item")
    todo_id = created["id"]

    assert delete_todo(todo_id) is True
    assert get_todo(todo_id) is None
    assert list_todos() == []
