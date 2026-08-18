"""App FastAPI y endpoints de la API de to-dos."""
import sqlite3
from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Query

from src.database import get_connection, init_db
from src.models import TodoCreate, TodoOut, TodoStatus, TodoUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="To-Do API", lifespan=lifespan)


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _row_to_todo(row: sqlite3.Row) -> TodoOut:
    return TodoOut(**dict(row))


def _get_todo_or_404(conn: sqlite3.Connection, todo_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    return row


@app.get("/api/todos", response_model=list[TodoOut])
def list_todos(
    status: TodoStatus | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[TodoOut]:
    if status is not None:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status = ? ORDER BY id", (status.value,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM todos ORDER BY id").fetchall()
    return [_row_to_todo(row) for row in rows]


@app.get("/api/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, conn: sqlite3.Connection = Depends(get_db)) -> TodoOut:
    row = _get_todo_or_404(conn, todo_id)
    return _row_to_todo(row)


@app.post("/api/todos", response_model=TodoOut, status_code=201)
def create_todo(todo: TodoCreate, conn: sqlite3.Connection = Depends(get_db)) -> TodoOut:
    cursor = conn.execute(
        "INSERT INTO todos (title, description) VALUES (?, ?)",
        (todo.title, todo.description),
    )
    conn.commit()
    row = _get_todo_or_404(conn, cursor.lastrowid)
    return _row_to_todo(row)


@app.patch("/api/todos/{todo_id}", response_model=TodoOut)
def update_todo(
    todo_id: int, todo: TodoUpdate, conn: sqlite3.Connection = Depends(get_db)
) -> TodoOut:
    _get_todo_or_404(conn, todo_id)

    fields = todo.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    if "status" in fields:
        fields["status"] = fields["status"].value if hasattr(fields["status"], "value") else fields["status"]

    set_clause = ", ".join(f"{field} = ?" for field in fields)
    values = list(fields.values()) + [todo_id]
    conn.execute(
        f"UPDATE todos SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    row = _get_todo_or_404(conn, todo_id)
    return _row_to_todo(row)


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, conn: sqlite3.Connection = Depends(get_db)) -> None:
    _get_todo_or_404(conn, todo_id)
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
