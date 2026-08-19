"""Tests de la API de to-dos: al menos un test por endpoint."""
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.database import init_db
from src.main import app, get_db


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test_todos.db"
    init_db(db_path)

    def override_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_sample_todo(client: TestClient, title: str = "Comprar leche", description: str | None = "2 litros"):
    return client.post("/api/todos", json={"title": title, "description": description})


def test_create_todo(client: TestClient):
    response = create_sample_todo(client)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Comprar leche"
    assert body["description"] == "2 litros"
    assert body["status"] == "pending"
    assert "id" in body


def test_create_todo_without_description(client: TestClient):
    response = client.post("/api/todos", json={"title": "Sin descripcion"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_todo_invalid_body(client: TestClient):
    response = client.post("/api/todos", json={"description": "falta title"})
    assert response.status_code == 422


def test_list_todos(client: TestClient):
    create_sample_todo(client, title="Tarea 1")
    create_sample_todo(client, title="Tarea 2")

    response = client.get("/api/todos")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_list_todos_filtered_by_status(client: TestClient):
    todo_id = create_sample_todo(client, title="Tarea pendiente").json()["id"]
    create_sample_todo(client, title="Otra tarea")
    client.patch(f"/api/todos/{todo_id}", json={"status": "done"})

    response = client.get("/api/todos", params={"status": "done"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == todo_id


def test_get_todo(client: TestClient):
    todo_id = create_sample_todo(client).json()["id"]

    response = client.get(f"/api/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["id"] == todo_id


def test_get_todo_not_found(client: TestClient):
    response = client.get("/api/todos/999")
    assert response.status_code == 404


def test_update_todo(client: TestClient):
    todo_id = create_sample_todo(client).json()["id"]

    response = client.patch(
        f"/api/todos/{todo_id}",
        json={"title": "Comprar leche deslactosada", "status": "done"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Comprar leche deslactosada"
    assert body["status"] == "done"


def test_update_todo_not_found(client: TestClient):
    response = client.patch("/api/todos/999", json={"title": "no existe"})
    assert response.status_code == 404


def test_update_todo_empty_body(client: TestClient):
    todo_id = create_sample_todo(client).json()["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={})
    assert response.status_code == 400


def test_delete_todo(client: TestClient):
    todo_id = create_sample_todo(client).json()["id"]

    response = client.delete(f"/api/todos/{todo_id}")
    assert response.status_code == 204

    response = client.get(f"/api/todos/{todo_id}")
    assert response.status_code == 404


def test_delete_todo_not_found(client: TestClient):
    response = client.delete("/api/todos/999")
    assert response.status_code == 404


def test_create_email_report_simulated_without_smtp(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    todo_id = create_sample_todo(client).json()["id"]
    client.patch(f"/api/todos/{todo_id}", json={"status": "done"})

    response = client.post(
        "/api/email-reports",
        json={"recipient": "consultor@empresa.com", "description": "Avance semanal"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "simulated"
    assert body["todo_count"] == 1
    assert body["todo_ids"] == str(todo_id)
    assert body["recipient"] == "consultor@empresa.com"
    assert body["description"] == "Avance semanal"


def test_create_email_report_invalid_recipient(client: TestClient):
    response = client.post("/api/email-reports", json={"recipient": "no-es-un-correo"})
    assert response.status_code == 422


def test_create_email_report_with_no_completed_todos(client: TestClient):
    create_sample_todo(client)

    response = client.post(
        "/api/email-reports", json={"recipient": "consultor@empresa.com"}
    )
    assert response.status_code == 201
    assert response.json()["todo_count"] == 0


def test_list_email_reports(client: TestClient):
    client.post("/api/email-reports", json={"recipient": "consultor@empresa.com"})
    client.post("/api/email-reports", json={"recipient": "otro@empresa.com"})

    response = client.get("/api/email-reports")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
