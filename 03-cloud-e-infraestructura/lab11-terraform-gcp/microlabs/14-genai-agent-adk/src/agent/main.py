"""Agente de soporte con Google ADK (Agent Development Kit) servido como Cloud Run function.

Conceptos:
  - Agent = modelo + instrucción + herramientas (funciones de Python con docstring y type hints)
  - Runner + SessionService = memoria de la conversación (aquí: Firestore vía session_id del cliente)
  - El agente decide qué herramienta usar y cuántas veces (razonamiento + acción)

POST {"message": "...", "session": "abc"}
"""

import asyncio
import json
import logging
import os

import functions_framework
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import firestore
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(message)s")
db = firestore.Client(database=os.environ["FIRESTORE_DATABASE"])
APP = "lab11-soporte"


# ---------------- Herramientas (el docstring es la descripción que ve el modelo) ----------------
def consultar_pedido(pedido_id: str) -> dict:
    """Devuelve estado, total y fecha estimada de entrega de un pedido. Usar cuando el cliente da un número de pedido."""
    doc = db.collection("pedidos").document(pedido_id.upper()).get()
    return doc.to_dict() if doc.exists else {"error": f"El pedido {pedido_id} no existe"}


def politica_devoluciones(categoria: str) -> dict:
    """Devuelve la política de devolución para una categoría de producto: electronica, ropa u hogar."""
    politicas = {
        "electronica": "30 días con empaque original; se revisa el equipo antes de reembolsar.",
        "ropa": "60 días sin uso y con etiquetas.",
        "hogar": "15 días; los muebles armados no tienen devolución.",
    }
    return {"categoria": categoria, "politica": politicas.get(categoria.lower(), "Categoría no encontrada")}


def crear_ticket(pedido_id: str, motivo: str) -> dict:
    """Crea un ticket de soporte humano. Usar SOLO si el cliente lo pide o si el problema no se resuelve con las otras herramientas."""
    ref = db.collection("tickets").add({"pedido_id": pedido_id, "motivo": motivo, "estado": "abierto",
                                        "creado": firestore.SERVER_TIMESTAMP})[1]
    return {"ticket_id": ref.id, "estado": "abierto"}


agent = Agent(
    name="agente_soporte",
    model=os.environ.get("MODEL", "gemini-2.5-flash"),
    description="Agente de soporte postventa de una tienda en línea.",
    instruction=(
        "Eres el agente de soporte de TiendaMX. Responde en español, breve y amable. "
        "Usa las herramientas para datos reales; nunca inventes estados de pedidos ni políticas. "
        "Si falta el número de pedido, pídelo. Antes de crear un ticket confirma el motivo con el cliente."
    ),
    tools=[consultar_pedido, politica_devoluciones, crear_ticket],
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name=APP, session_service=session_service)


async def run_turn(user_id, session_id, message):
    session = await session_service.get_session(app_name=APP, user_id=user_id, session_id=session_id)
    if session is None:
        await session_service.create_session(app_name=APP, user_id=user_id, session_id=session_id)

    tool_calls, answer = [], ""
    content = types.Content(role="user", parts=[types.Part(text=message)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        for call in event.get_function_calls() or []:
            tool_calls.append({"tool": call.name, "args": dict(call.args or {})})
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(p.text or "" for p in event.content.parts)
    return answer, tool_calls


@functions_framework.http
def handler(request):
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return ({"error": "message es requerido"}, 400)
    session_id = body.get("session", "default")

    answer, tool_calls = asyncio.run(run_turn("cliente", session_id, message))
    logging.info(json.dumps({"severity": "INFO", "session": session_id, "tool_calls": tool_calls}))
    return {"answer": answer, "tool_calls": tool_calls}
