"""Pydantic schemas for request validation and response serialization."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    """Payload for creating a new todo."""

    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped


class TodoUpdate(BaseModel):
    """Payload for updating an existing todo."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped


class TodoResponse(BaseModel):
    """Todo returned to API clients."""

    id: str
    title: str
    description: Optional[str]
    completed: bool
