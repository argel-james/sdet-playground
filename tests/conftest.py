"""Shared pytest fixtures for test isolation."""

import pytest

from app.service import reset_store


@pytest.fixture(autouse=True)
def clean_store():
    """Reset in-memory state before each test.

    Quality risk without this: tests leak data into each other, causing flaky
    automation that erodes trust in the CI gate before release.
    """
    reset_store()
    yield
    reset_store()
