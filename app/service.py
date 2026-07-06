"""Business logic for the Todo API.

This module holds the core rules (duplicates, validation, CRUD) separate from
HTTP routing so unit tests can verify logic in isolation.
"""

import uuid
from typing import Any, Dict, List, Optional

# In-memory store keyed by todo ID. In production this would be a database.
_store: Dict[str, Dict[str, Any]] = {}


class DuplicateTitleError(Exception):
    """Raised when a todo title already exists."""


class EmptyTitleError(Exception):
    """Raised when a title is empty after stripping whitespace."""


def reset_store() -> None:
    """Clear all todos. Used by tests to ensure isolated, repeatable runs."""
    _store.clear()


def _title_exists(title: str, exclude_id: Optional[str] = None) -> bool:
    for todo_id, todo in _store.items():
        if exclude_id and todo_id == exclude_id:
            continue
        if todo["title"].lower() == title.lower():
            return True
    return False


def create_todo(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new todo and return its data."""
    normalized_title = title.strip()
    if not normalized_title:
        raise EmptyTitleError("Title cannot be empty")

    if _title_exists(normalized_title):
        raise DuplicateTitleError(f"Todo with title '{normalized_title}' already exists")

    todo_id = str(uuid.uuid4())
    todo = {
        "id": todo_id,
        "title": normalized_title,
        "description": description,
        "completed": False,
    }
    _store[todo_id] = todo
    return todo


def list_todos() -> List[Dict[str, Any]]:
    """Return all todos."""
    return list(_store.values())


def get_todo(todo_id: str) -> Optional[Dict[str, Any]]:
    """Return a single todo by ID, or None if not found."""
    return _store.get(todo_id)


def update_todo(
    todo_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """Update fields on an existing todo. Returns None if the todo does not exist."""
    todo = _store.get(todo_id)
    if todo is None:
        return None

    if title is not None:
        normalized_title = title.strip()
        if not normalized_title:
            raise EmptyTitleError("Title cannot be empty")
        if _title_exists(normalized_title, exclude_id=todo_id):
            raise DuplicateTitleError(f"Todo with title '{normalized_title}' already exists")
        todo["title"] = normalized_title

    if description is not None:
        todo["description"] = description

    if completed is not None:
        todo["completed"] = completed

    return todo


def delete_todo(todo_id: str) -> bool:
    """Delete a todo by ID. Returns False if the todo does not exist."""
    if todo_id not in _store:
        return False

    # del _store[todo_id]
    # FIXME: Intentional bug for SDET demo — see BUG_REPORT.md
    # Should be: del _store[todo_id]  (or _store.pop(todo_id))
    # BUG: returns success without removing the item from the store.
    return True
