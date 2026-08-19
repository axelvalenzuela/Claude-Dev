"""Panel de control Streamlit para la API de to-dos (FastAPI + SQLite)."""
import os

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.environ.get("TODO_API_URL", "http://127.0.0.1:8000/api/todos")

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


def todos_to_dataframe(todos: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(todos)
    if df.empty:
        return df
    df["status"] = df["status"].map(STATUS_LABELS).fillna(df["status"])
    df = df.rename(
        columns={
            "id": "ID",
            "title": "Título",
            "description": "Descripción",
            "status": "Estado",
            "created_at": "Creada",
            "updated_at": "Actualizada",
        }
    )
    df["Descripción"] = df["Descripción"].fillna("—")
    return df[["ID", "Título", "Descripción", "Estado", "Creada", "Actualizada"]]


st.title("✅ To-Do Dashboard")

try:
    todos = fetch_todos()
except requests.exceptions.RequestException as exc:
    st.error(f"No se pudo conectar con la API en {API_BASE_URL}. ¿Está corriendo uvicorn?\n\n{exc}")
    st.stop()

tab_dashboard, tab_registros = st.tabs(["📊 Dashboard", "📋 Registros"])

with tab_dashboard:
    total = len(todos)
    done_count = sum(1 for t in todos if t["status"] == "done")
    pending_count = total - done_count

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("Pendientes", pending_count)
    col3.metric("Completadas", done_count)

    if total:
        st.divider()
        st.subheader("Resumen por estado")
        summary_df = pd.DataFrame(
            {"Estado": ["Pendiente", "Completada"], "Cantidad": [pending_count, done_count]}
        ).set_index("Estado")
        st.bar_chart(summary_df)

with tab_registros:
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
    st.subheader("Tareas registradas")

    if not todos:
        st.info("No hay tareas todavía. Crea una arriba.")
    else:
        st.dataframe(todos_to_dataframe(todos), hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("Acciones")
        options = {f"#{t['id']} — {t['title']}": t for t in todos}
        selected_label = st.selectbox("Selecciona una tarea", options.keys())
        selected_todo = options[selected_label]

        action_col1, action_col2 = st.columns(2)
        if selected_todo["status"] == "pending":
            if action_col1.button("✅ Marcar como completada"):
                try:
                    mark_done(selected_todo["id"])
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"No se pudo actualizar la tarea: {exc}")
        else:
            action_col1.write("Ya completada")

        if action_col2.button("🗑️ Eliminar tarea"):
            try:
                delete_todo(selected_todo["id"])
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"No se pudo eliminar la tarea: {exc}")
