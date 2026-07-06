# Bug Report: DELETE /todos/{id} returns success but does not remove the todo

## Title

DELETE endpoint reports success (204) without removing todo from storage

## Environment

- Project: SDET Mini Project — Todo API
- Component: `app/service.py` → `delete_todo()`
- Endpoint: `DELETE /todos/{id}`

## Steps to Reproduce

1. Start the API (or use the test client).
2. Create a todo:
   ```bash
   curl -X POST http://localhost:8000/todos \
     -H "Content-Type: application/json" \
     -d '{"title": "Test item"}'
   ```
3. Note the `id` from the response.
4. Delete the todo:
   ```bash
   curl -X DELETE http://localhost:8000/todos/{id}
   ```
   Response: `204 No Content` (appears successful).
5. Fetch the same todo:
   ```bash
   curl http://localhost:8000/todos/{id}
   ```

## Expected Result

- `DELETE` returns `204 No Content`.
- Subsequent `GET /todos/{id}` returns `404 Not Found`.
- `GET /todos` no longer includes the deleted item.

## Actual Result

- `DELETE` returns `204 No Content`.
- `GET /todos/{id}` still returns `200` with the todo data.
- `GET /todos` still lists the "deleted" item.

## Root Cause

In `app/service.py`, `delete_todo()` checks that the ID exists and returns `True`, but never removes the entry from `_store`:

```python
def delete_todo(todo_id: str) -> bool:
    if todo_id not in _store:
        return False
    # BUG: should call del _store[todo_id] or _store.pop(todo_id)
    return True
```

## Impact

| Area | Impact |
|------|--------|
| User experience | Users believe items are deleted but they persist in lists |
| Data integrity | Storage grows with "ghost" records; list views show stale data |
| Integrations | Clients that trust the 204 status will have inconsistent local vs server state |
| Progressive release | Bug could reach production users if only status-code tests run |

**Severity:** High — silent data corruption with a misleading success signal.

## Reproducible

**Yes** — 100% reproducible on every delete operation.

## Could This Be a Regression?

**Yes.** Delete is a frequently touched code path during refactors (e.g., switching from in-memory to database storage, adding soft-delete flags, or AI-assisted rewrites). A change that preserves the return value but drops the actual removal would pass shallow "returns 204" checks.

## Evidence from Failing Tests

Run `make test` from the project root. Three tests fail:

```
tests/test_unit_service.py::test_delete_todo_removes_item FAILED
tests/test_api.py::test_delete_returns_204_but_item_still_exists FAILED
tests/test_e2e_workflow.py::test_full_todo_lifecycle FAILED
```

Example failure (unit test):

```
assert get_todo(todo_id) is None
E   AssertionError: assert {'id': '...', 'title': 'Remove obsolete item', ...} is None
```

Example failure (E2E workflow — final step):

```
assert final_get.status_code == 404
E   AssertionError: Workflow failed at final step: item still exists after delete.
```

## Suggested Fix

```python
def delete_todo(todo_id: str) -> bool:
    if todo_id not in _store:
        return False
    del _store[todo_id]
    return True
```

## SDET Takeaway

This bug demonstrates why **behavioral assertions** matter more than **status-code-only checks**. An API test that only asserts `response.status_code == 204` would pass. The SDET adds a follow-up `GET` to verify state — catching silent regressions before they reach users during progressive release.
