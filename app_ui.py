"""Panel de control Streamlit para la API de to-dos (FastAPI + SQLite)."""
import os

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.environ.get("TODO_API_URL", "http://127.0.0.1:8000/api/todos")
EMAIL_REPORTS_URL = os.environ.get(
    "EMAIL_REPORTS_API_URL", API_BASE_URL.rsplit("/todos", 1)[0] + "/email-reports"
)

STATUS_LABELS = {"pending": "Pendiente", "done": "Completada"}
EMAIL_STATUS_LABELS = {
    "sent": "Enviado",
    "simulated": "Simulado (SMTP no configurado)",
    "failed": "Falló",
}

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


def fetch_email_reports() -> list[dict]:
    response = requests.get(EMAIL_REPORTS_URL, timeout=5)
    response.raise_for_status()
    return response.json()


def send_email_report(recipient: str, description: str | None) -> dict:
    response = requests.post(
        EMAIL_REPORTS_URL,
        json={"recipient": recipient, "description": description},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


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


def email_reports_to_dataframe(reports: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(reports)
    if df.empty:
        return df
    df["status"] = df["status"].map(EMAIL_STATUS_LABELS).fillna(df["status"])
    df = df.rename(
        columns={
            "id": "ID",
            "recipient": "Destinatario",
            "description": "Descripción para el consultor",
            "todo_ids": "Tareas incluidas (IDs)",
            "todo_count": "# Tareas",
            "status": "Estado",
            "error_message": "Detalle del error",
            "sent_at": "Fecha de envío",
        }
    )
    df["Descripción para el consultor"] = df["Descripción para el consultor"].fillna("—")
    df["Detalle del error"] = df["Detalle del error"].fillna("—")
    return df[
        [
            "ID",
            "Fecha de envío",
            "Destinatario",
            "# Tareas",
            "Tareas incluidas (IDs)",
            "Estado",
            "Descripción para el consultor",
            "Detalle del error",
        ]
    ]


st.title("✅ To-Do Dashboard")

try:
    todos = fetch_todos()
except requests.exceptions.RequestException as exc:
    st.error(f"No se pudo conectar con la API en {API_BASE_URL}. ¿Está corriendo uvicorn?\n\n{exc}")
    st.stop()

tab_dashboard, tab_registros, tab_reporte = st.tabs(
    ["📊 Dashboard", "📋 Registros", "📧 Reporte por correo"]
)

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
        st.dataframe(todos_to_dataframe(todos), hide_index=True, width="stretch")

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

with tab_reporte:
    completed_todos = [t for t in todos if t["status"] == "done"]

    st.subheader("Actividades completadas a incluir")
    if not completed_todos:
        st.info("No hay actividades completadas todavía.")
    else:
        st.dataframe(
            todos_to_dataframe(completed_todos),
            hide_index=True,
            width="stretch",
        )

    st.divider()
    st.subheader("Enviar reporte")

    if not os.environ.get("SMTP_HOST"):
        st.warning(
            "SMTP_HOST no está configurado: el envío quedará en modo simulado "
            "(se registra en la base de datos pero no sale un correo real). "
            "Configura SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM "
            "como variables de entorno para enviar correos reales."
        )

    with st.form("email_report_form", clear_on_submit=True):
        recipient = st.text_input("Correo del consultor")
        report_description = st.text_area(
            "Describe este envío para tu consultor",
            height=100,
            placeholder="Ej. Avance semanal de migración, entregado antes del corte del viernes.",
        )
        send_submitted = st.form_submit_button("📧 Enviar reporte")
        if send_submitted:
            if not recipient.strip():
                st.warning("El correo del consultor es obligatorio.")
            else:
                try:
                    result = send_email_report(
                        recipient.strip(), report_description.strip() or None
                    )
                    if result["status"] == "sent":
                        st.success(f"Reporte enviado a {recipient.strip()}.")
                    elif result["status"] == "simulated":
                        st.info(
                            f"Reporte registrado para {recipient.strip()} en modo "
                            "simulado (configura SMTP para enviarlo de verdad)."
                        )
                    else:
                        st.error(f"El envío falló: {result.get('error_message')}")
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"No se pudo registrar el envío: {exc}")

    st.divider()
    st.subheader("Historial de envíos")

    try:
        email_reports = fetch_email_reports()
    except requests.exceptions.RequestException as exc:
        st.error(f"No se pudo cargar el historial de envíos: {exc}")
    else:
        if not email_reports:
            st.info("Todavía no se ha registrado ningún envío.")
        else:
            st.dataframe(
                email_reports_to_dataframe(email_reports),
                hide_index=True,
                width="stretch",
            )
