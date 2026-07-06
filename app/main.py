"""FastAPI application exposing the Todo API endpoints."""

from typing import Dict, List

from fastapi import FastAPI, HTTPException, status

from app.models import TodoCreate, TodoResponse, TodoUpdate
from app.service import (
    DuplicateTitleError,
    EmptyTitleError,
    create_todo,
    delete_todo,
    get_todo,
    list_todos,
    update_todo,
)

app = FastAPI(
    title="SDET Todo API",
    description="A minimal Todo API for learning SDET testing practices.",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Smoke-test endpoint for CI and deployment health checks."""
    return {"status": "ok"}


@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo_endpoint(payload: TodoCreate) -> dict:
    try:
        return create_todo(title=payload.title, description=payload.description)
    except DuplicateTitleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmptyTitleError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@app.get("/todos", response_model=List[TodoResponse])
def list_todos_endpoint() -> List[dict]:
    return list_todos()


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo_endpoint(todo_id: str) -> dict:
    todo = get_todo(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(todo_id: str, payload: TodoUpdate) -> dict:
    try:
        todo = update_todo(
            todo_id=todo_id,
            title=payload.title,
            description=payload.description,
            completed=payload.completed,
        )
    except DuplicateTitleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmptyTitleError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_endpoint(todo_id: str) -> None:
    deleted = delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
