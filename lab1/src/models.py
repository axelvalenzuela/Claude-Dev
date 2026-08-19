"""Modelos Pydantic para validación de inputs y outputs de la API de to-dos."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


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


class EmailReportStatus(str, Enum):
    sent = "sent"
    simulated = "simulated"
    failed = "failed"


class EmailReportCreate(BaseModel):
    recipient: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("recipient debe ser un correo válido")
        return value


class EmailReportOut(BaseModel):
    id: int
    recipient: str
    description: str | None
    todo_ids: str
    todo_count: int
    status: EmailReportStatus
    error_message: str | None
    sent_at: datetime
