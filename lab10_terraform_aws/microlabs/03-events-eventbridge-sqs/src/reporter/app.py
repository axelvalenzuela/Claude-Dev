"""Tarea programada invocada por EventBridge Scheduler."""

import json
import logging

logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context):
    logger.info(json.dumps({"msg": "scheduled report", "input": event}))
    return {"status": "ok"}
