# Test Plan: Todo CRUD API

## Feature Under Test

A minimal REST API for managing todos (create, read, update, delete). This mirrors how product teams expose capabilities to clients through REST endpoints consumed by web apps, mobile clients, and integrations.

## Acceptance Criteria

1. **Create** — `POST /todos` with a valid title returns `201` and a todo with a unique `id`.
2. **Read** — `GET /todos/{id}` returns `200` for existing todos; `GET /todos` lists all items.
3. **Update** — `PUT /todos/{id}` modifies title, description, and `completed` status.
4. **Delete** — `DELETE /todos/{id}` removes the todo; subsequent `GET` returns `404`.
5. **Validation** — Empty, missing, or whitespace-only titles return `422`.
6. **Duplicates** — Creating or renaming to an existing title returns `409 Conflict`.

## Test Scenarios

| Scenario | Test Layer | File |
|----------|------------|------|
| Create with valid data | Unit + API | `test_unit_service.py`, `test_api.py` |
| Title whitespace trimming | Unit | `test_unit_service.py` |
| Reject duplicate title | Unit + API | `test_unit_service.py`, `test_api.py` |
| Reject empty title | Unit + API | `test_unit_service.py`, `test_api.py` |
| Get / update / delete not found | Unit + API | `test_unit_service.py`, `test_api.py` |
| Full CRUD lifecycle | E2E workflow | `test_e2e_workflow.py` |
| Health check smoke | API | `test_api.py` |
| AI-reviewed negative API cases | API | `test_api_ai_reviewed.py` (see `AI_TESTING_REVIEW.md`) |
| Continuous testing on push/PR | CI | `.github/workflows/ci.yml` |
| Code coverage report | Automation | `make coverage` (`pytest --cov=app`) |

## Edge Cases

| Edge Case | Expected Behavior | Why It Matters |
|-----------|-------------------|----------------|
| Whitespace-only title `"   "` | `422` rejection | Prevents unnamed records in lists |
| Duplicate title (case-insensitive) | `409` rejection | Prevents ambiguous item targeting |
| Delete non-existent ID | `404` | Clear signal for stale client state |
| Update to another todo's title | `409` rejection | Data integrity across rename operations |
| Delete then GET | `404` | Confirms state actually changed |

## Regression Risks

| Risk | What Could Break | Mitigation |
|------|------------------|------------|
| Delete silently fails | Item remains after `204` response | `test_delete_todo_removes_item`, `test_delete_returns_204_but_item_still_exists`, `test_full_todo_lifecycle` |
| Duplicate guard bypass | Two todos share one title | Duplicate tests at unit and API layers |
| Title trimming removed | Whitespace duplicates slip through | `test_create_todo_strips_whitespace` |
| Status code drift | Clients parse wrong responses | API contract tests on every endpoint |

## Definition of Done

- [ ] All automated tests pass (`make test` exits with code 0)
- [ ] Acceptance criteria verified by at least one test each
- [ ] Known bugs documented in `BUG_REPORT.md` or fixed
- [ ] Test plan updated if new scenarios are added
- [ ] README run instructions verified on a clean environment

## Bugs Found

| Bug | Severity | Found By | Status |
|-----|----------|----------|--------|
| `delete_todo()` returns success without removing item from store | High | `test_delete_todo_removes_item`, `test_delete_returns_204_but_item_still_exists`, `test_full_todo_lifecycle` | Open (intentional for demo) |

### How to verify the delete bug

```bash
cd sdet-mini-project
make test
```

Expected: 3 tests fail, all related to delete not removing state. See `BUG_REPORT.md` for full details.

### How to fix (exercise)

In `app/service.py`, replace the buggy `delete_todo` with:

```python
def delete_todo(todo_id: str) -> bool:
    if todo_id not in _store:
        return False
    del _store[todo_id]
    return True
```

Re-run `make test` — all tests should pass.
