# AI-Assisted Test Review Log

This document records how an SDET would **use AI to accelerate test design** while still applying human judgment — generating ideas quickly, then validating each one before it lands in the suite.

---

## Context

**Feature:** Todo CRUD API (`POST/GET/PUT/DELETE /todos`)  
**AI tool used (example):** Cursor / GitHub Copilot-style prompt  
**Human reviewer role:** SDET validating against `TEST_PLAN.md` acceptance criteria  
**Output file:** `tests/test_api_ai_reviewed.py`

### Prompt given to AI (example)

```text
Generate pytest API negative tests for a FastAPI Todo API.
Endpoints: POST/GET/PUT/DELETE /todos.
Cover invalid input, missing fields, wrong types, boundary values, and error scenarios.
Use FastAPI TestClient. Add comments explaining each test.
```

---

## Review Summary

| AI suggestion | Decision | Rationale |
|---------------|----------|-----------|
| Title > 100 chars → `422` | **KEPT** | Boundary validation; in `TEST_PLAN.md` edge cases |
| Empty JSON body on POST → `422` | **KEPT** | Real client mistake; must not 500 |
| Title as integer → `422` | **KEPT** | Type validation at API boundary |
| Whitespace title on PUT → `422` | **KEPT** | Symmetric with POST; rename-to-blank is realistic |
| `title: null` on POST → `422` | **KEPT** | Null ≠ missing; both must fail safely |
| DELETE returns 500 when DB is down | **REJECTED** | No database in this project; needs mocks — out of scope |
| GET /health responds in < 100ms | **REJECTED** | Performance testing is a separate concern; not this suite |
| Test OPTIONS / CORS headers | **REJECTED** | CORS not implemented; testing unbuilt features adds noise |
| Assert `detail` message exact string on 409 | **REJECTED** | Too brittle; status code + keyword is enough for regression |
| Fuzz test 1000 random payloads | **REJECTED** | Valuable later with hypothesis library; overkill for mini project |
| Soft-delete flag after DELETE | **REJECTED** | Feature does not exist; AI hallucinated requirements |

---

## Examples of Human Review in Practice

### KEPT: `test_create_todo_title_too_long_returns_422`

**AI output:** Send 101-character title, expect 422.

**Why kept:** `TodoCreate` defines `max_length=100`. This maps to acceptance criterion #5 (validation). A client form or plugin could send oversized strings.

**Quality risk:** Unvalidated length breaks storage limits and UI rendering in production systems.

### REJECTED: Database failure → 500 on DELETE

**AI output:**

```python
@patch("app.service._store", side_effect=ConnectionError)
def test_delete_database_down_returns_500():
    ...
```

**Why rejected:**

- This project uses in-memory storage, not a database.
- The test would mock infrastructure that does not exist — **false confidence**.
- Performance/resilience testing belongs in a separate suite with real dependencies.

**Principle:** Do not test imaginary architecture. Align tests to actual design.

### REJECTED: Performance assertion on `/health`

**AI output:** `assert response.elapsed.total_seconds() < 0.1`

**Why rejected:**

- `TestClient` is in-process; timing is not representative of production.
- Performance testing needs dedicated tooling (k6, Locust, JMeter) and environments.
- Would be **flaky** in CI.

**Principle:** Right test type, right layer. API contract tests ≠ performance tests.

---

## What Landed in the Repo

Five reviewed tests in `tests/test_api_ai_reviewed.py`:

1. `test_create_todo_title_too_long_returns_422`
2. `test_create_todo_empty_json_body_returns_422`
3. `test_create_todo_title_wrong_type_returns_422`
4. `test_update_todo_whitespace_title_returns_422`
5. `test_create_todo_null_title_returns_422`

Each includes inline comments for **what** is verified and **quality risk** covered.

---

## Talking Points

**"How do you use AI in testing?"**

> "I use AI to draft test ideas and boilerplate quickly, then review each suggestion against acceptance criteria, system design, and flakiness risk. I kept validation and type-safety tests that match real client errors. I rejected database-failure and performance tests because they don't match this API's architecture or belong in a different test layer."

**"How do you validate AI-generated code?"**

> "Same as any code — run it. In this project, `delete_todo` returns True but never deletes. Tests caught that. AI output still needs execution, review, and maintenance."

---

## Next Steps (Optional)

- Re-run AI prompt after fixing `delete_todo()` and ask for **regression** test ideas only.
- Add `pytest-cov` threshold in CI once coverage baseline is agreed with the team.
- Expand performance tests in a separate pipeline when a staging environment exists.
