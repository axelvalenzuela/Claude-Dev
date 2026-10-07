"""Chat protegido: Model Armor revisa el prompt ANTES de Gemini y la respuesta DESPUÉS.

POST {"message": "..."} -> {"answer", "blocked", "stage", "findings"}
"""

import json
import logging
import os

import functions_framework
from google import genai
from google.cloud import modelarmor_v1

logging.basicConfig(level=logging.INFO, format="%(message)s")

TEMPLATE = os.environ["TEMPLATE"]
armor = modelarmor_v1.ModelArmorClient(
    client_options={"api_endpoint": f"modelarmor.{os.environ['ARMOR_LOCATION']}.rep.googleapis.com"})
llm = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ["VERTEX_LOCATION"])
BLOCKED = "No puedo procesar esta solicitud por políticas de seguridad."


def findings(result):
    """Lista de filtros que encontraron coincidencias (pi_and_jailbreak, rai, sdp, malicious_uris...)."""
    data = type(result).to_dict(result, use_integers_for_enums=False)
    filters = data.get("sanitization_result", {}).get("filter_results", {})
    return [name for name, value in filters.items() if "MATCH_FOUND" in json.dumps(value)]


def is_blocked(result):
    return result.sanitization_result.filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND


@functions_framework.http
def handler(request):
    message = ((request.get_json(silent=True) or {}).get("message") or "").strip()
    if not message:
        return ({"error": "message es requerido"}, 400)

    # 1. Revisión de la ENTRADA (prompt injection, jailbreak, datos sensibles, URLs maliciosas)
    prompt_check = armor.sanitize_user_prompt(request=modelarmor_v1.SanitizeUserPromptRequest(
        name=TEMPLATE, user_prompt_data=modelarmor_v1.DataItem(text=message)))
    if is_blocked(prompt_check):
        hits = findings(prompt_check)
        logging.warning(json.dumps({"severity": "WARNING", "stage": "prompt", "findings": hits}))
        return {"answer": BLOCKED, "blocked": True, "stage": "prompt", "findings": hits}

    # 2. Modelo
    answer = llm.models.generate_content(model=os.environ["MODEL"], contents=message).text or ""

    # 3. Revisión de la SALIDA (el modelo también puede filtrar datos o generar contenido dañino)
    response_check = armor.sanitize_model_response(request=modelarmor_v1.SanitizeModelResponseRequest(
        name=TEMPLATE, model_response_data=modelarmor_v1.DataItem(text=answer), user_prompt=message))
    if is_blocked(response_check):
        hits = findings(response_check)
        logging.warning(json.dumps({"severity": "WARNING", "stage": "response", "findings": hits}))
        return {"answer": BLOCKED, "blocked": True, "stage": "response", "findings": hits}

    return {"answer": answer, "blocked": False, "stage": None, "findings": []}
