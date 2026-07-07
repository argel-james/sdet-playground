# SDET Guide — Concepts Demonstrated by This Project

This document explains **what an SDET does** and how this repository demonstrates those practices. For setup and usage, see [README.md](README.md).

---

## What Does an SDET Do?

An SDET sits at the intersection of development and quality engineering:

| Responsibility | In This Project |
|----------------|-----------------|
| Design test strategy | Unit, API, and E2E layers in `tests/` |
| Automate verification | `pytest` suite runnable via `make test` |
| Document quality risks | Comments in tests, `TEST_PLAN.md` |
| Report defects clearly | `BUG_REPORT.md` with repro steps and evidence |
| Act as quality gatekeeper | GitHub Actions CI + `make test` pass/fail gate |
| Use & review AI-generated tests | `AI_TESTING_REVIEW.md`, `test_api_ai_reviewed.py` |
| Code coverage analysis | `make coverage` (`pytest --cov=app`) |
| Think in user workflows | `test_e2e_workflow.py` chains create → read → update → delete |

SDETs don't just "click around." They build **repeatable automation** that catches regressions before customers do.

---

## Test Types in This Project

```text
        ┌─────────────────┐
        │  E2E Workflow   │  Few tests, full user journey
        │ test_e2e_*.py   │
        ├─────────────────┤
        │  API / Integration │  HTTP contracts, status codes
        │  test_api.py    │
        ├─────────────────┤
        │  Unit Tests     │  Fast, isolated business logic
        │ test_unit_*.py  │
        └─────────────────┘
```

### Unit tests (`tests/test_unit_service.py`)

- Call `app/service.py` functions directly — no HTTP.
- **Fast** and **precise**: a failure points to the exact function.
- Example: "Does `create_todo` reject duplicate titles?"
- **Limitation:** does not prove routes, JSON parsing, or status codes are wired correctly.

### API / integration tests (`tests/test_api.py`)

- Use FastAPI `TestClient` to call endpoints like an external client would.
- Verify routing, request validation, HTTP status codes, and response bodies together.
- Example: "Does `POST /todos` with a duplicate title return `409`?"
- **Closer to reality** for teams shipping APIs consumed by plugins, web apps, or microservices.

### End-to-end workflow tests (`tests/test_e2e_workflow.py`)

- Chain multiple API calls into one realistic user journey.
- Example: create → get → update → get → delete → confirm gone.
- **How SDETs think:** Users don't validate one endpoint at a time — they run full workflows. Quality means the **whole journey** works across a release.

---

## SDET as Quality Gatekeeper

Before a build moves from internal → staging → production (progressive release), an SDET asks:

1. Does the automated suite pass? (`make test` exit code `0`)
2. Are known bugs documented or fixed?
3. Do workflow tests cover the features being shipped?

If tests fail, the release **stops**. This is the quality gate — automation gives confidence that a change didn't break existing behavior (regression testing).

---

## Regression Testing and Progressive Release

| Concept | How This Project Shows It |
|---------|---------------------------|
| **Regression** | A change to `delete_todo` breaks delete without anyone noticing — unless tests re-run |
| **Automation** | `make test` runs the full suite in seconds |
| **Gate** | Non-zero exit code blocks merge/deploy |
| **Progressive release** | Fix bugs while suite is red → turn green → safe to widen rollout |

In practice: a hotfix might pass code review but fail workflow tests if delete no longer removes data. Automation catches that before wider rollout.

---

## AI-Generated Code Still Needs Verification

AI (and Copilot-style tools) can produce code that **looks correct**:

- `delete_todo` has the right signature
- It returns `True` on success
- The route returns `204 No Content`

But **running tests** reveals the item was never removed. This project includes an intentional bug to demonstrate that:

> Correct-looking code ≠ correct behavior. Always run the test suite.

### AI-assisted test design (with human review)

See **`AI_TESTING_REVIEW.md`** for a full log of AI-suggested tests — what was **kept**, **rejected**, and **why**.

Implemented reviewed tests live in `tests/test_api_ai_reviewed.py` — AI drafts ideas, a human reviews them before merge.

---

## How to Know If the Build Is Passing or Failing

| Signal | Passing | Failing |
|--------|---------|---------|
| `make test` exit code | `0` | non-zero (e.g., `1`) |
| pytest summary | `X passed` | `Y failed, Z passed` |
| `make coverage` | High % on `app/service.py`, `app/main.py` | Gaps highlight untested branches |
| GitHub Actions CI | Green check | Red X — merge blocked |

Example failing output (abbreviated):

```text
====== short test summary info ======
FAILED tests/test_unit_service.py::test_delete_todo_removes_item
FAILED tests/test_api.py::test_delete_returns_204_but_item_still_exists
FAILED tests/test_e2e_workflow.py::test_full_todo_lifecycle
3 failed, 26 passed
```

An SDET or developer seeing this knows: **do not release** until the delete bug is fixed and tests are green.

---

## Fix the Bug (Learning Exercise)

1. Read `BUG_REPORT.md`
2. Open `app/service.py` and fix `delete_todo()`
3. Run `make test` — all tests should pass
4. Compare how unit, API, and E2E tests all contributed to finding the same defect at different layers

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start |
| [TEST_PLAN.md](TEST_PLAN.md) | Formal test plan |
| [BUG_REPORT.md](BUG_REPORT.md) | Sample defect report |
| [AI_TESTING_REVIEW.md](AI_TESTING_REVIEW.md) | AI test review log |
