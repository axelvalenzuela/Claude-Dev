"""Panel de control Streamlit para la API de to-dos (FastAPI + SQLite)."""
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("TODO_API_URL", "http://127.0.0.1:8000/api/todos")

STATUS_COLORS = {"pending": "#f0ad4e", "done": "#5cb85c"}
STATUS_LABELS = {"pending": "Pendiente", "done": "Completada"}

st.set_page_config(page_title="To-Do Dashboard", page_icon="✅", layout="wide")


def fetch_todos() -> list[dict]:
    response = requests.get(API_BASE_URL, timeout=5)
    response.raise_for_status()
    return response.json()


def create_todo(title: str, description: str | None) -> None:
    response = requests.post(
        API_BASE_URL, json={"title": title, "description": description}, timeout=5
    )
    response.raise_for_status()


def mark_done(todo_id: int) -> None:
    response = requests.patch(f"{API_BASE_URL}/{todo_id}", json={"status": "done"}, timeout=5)
    response.raise_for_status()


def delete_todo(todo_id: int) -> None:
    response = requests.delete(f"{API_BASE_URL}/{todo_id}", timeout=5)
    response.raise_for_status()


st.title("✅ To-Do Dashboard")

try:
    todos = fetch_todos()
except requests.exceptions.RequestException as exc:
    st.error(f"No se pudo conectar con la API en {API_BASE_URL}. ¿Está corriendo uvicorn?\n\n{exc}")
    st.stop()

total = len(todos)
done_count = sum(1 for t in todos if t["status"] == "done")
pending_count = total - done_count

col1, col2, col3 = st.columns(3)
col1.metric("Total", total)
col2.metric("Pendientes", pending_count)
col3.metric("Completadas", done_count)

st.divider()
st.subheader("Nueva tarea")

with st.form("new_todo_form", clear_on_submit=True):
    title = st.text_input("Título")
    description = st.text_area("Descripción", height=80)
    submitted = st.form_submit_button("Crear tarea")
    if submitted:
        if not title.strip():
            st.warning("El título es obligatorio.")
        else:
            try:
                create_todo(title.strip(), description.strip() or None)
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"No se pudo crear la tarea: {exc}")

st.divider()
st.subheader("Tareas")

if not todos:
    st.info("No hay tareas todavía. Crea una arriba.")
else:
    header = st.columns([0.6, 2, 3, 1.4, 1.1, 1.1])
    for col, label in zip(header, ["ID", "Título", "Descripción", "Estado", "Completar", "Eliminar"]):
        col.markdown(f"**{label}**")

    for todo in todos:
        row = st.columns([0.6, 2, 3, 1.4, 1.1, 1.1])
        row[0].write(todo["id"])
        row[1].write(todo["title"])
        row[2].write(todo["description"] or "—")

        color = STATUS_COLORS[todo["status"]]
        label = STATUS_LABELS[todo["status"]]
        row[3].markdown(
            f'<span style="background-color:{color};color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:0.85em;">{label}</span>',
            unsafe_allow_html=True,
        )

        if todo["status"] == "pending":
            if row[4].button("✅", key=f"done_{todo['id']}", help="Marcar como completada"):
                try:
                    mark_done(todo["id"])
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"No se pudo actualizar la tarea: {exc}")
        else:
            row[4].write("—")

        if row[5].button("🗑️", key=f"delete_{todo['id']}", help="Eliminar tarea"):
            try:
                delete_todo(todo["id"])
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"No se pudo eliminar la tarea: {exc}")
