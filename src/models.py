"""Modelos Pydantic para validación de inputs y outputs de la API de to-dos."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    pending = "pending"
    done = "done"


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TodoStatus | None = None


class TodoOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: TodoStatus
    created_at: datetime
    updated_at: datetime
