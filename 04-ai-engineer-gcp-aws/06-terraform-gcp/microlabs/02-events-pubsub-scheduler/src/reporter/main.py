"""Tarea programada por Cloud Scheduler (HTTP + OIDC)."""

import json
import logging

import functions_framework

logging.basicConfig(level=logging.INFO, format="%(message)s")


@functions_framework.http
def handler(request):
    logging.info(json.dumps({"severity": "INFO", "msg": "scheduled report", "input": request.get_json(silent=True)}))
    return {"status": "ok"}
