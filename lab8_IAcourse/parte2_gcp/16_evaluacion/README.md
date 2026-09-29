# 16 — Evaluar la IA con métricas y un quality gate en CI

**Qué aprendes:** cómo saber, con números, si un cambio de prompt o de modelo mejora o empeora
el sistema, y cómo impedir que un cambio malo llegue a `main`.

## Conceptos

| Tipo de prueba | Qué verifica | Dónde |
|---|---|---|
| Tests unitarios | Piezas deterministas (guardrails, comparador, costos) | [tests/](../tests/) |
| Tests de flujo | El pipeline completo en simulado | [tests/test_flujos.py](../tests/test_flujos.py) |
| Evaluación (golden set) | Calidad de la IA con casos de respuesta conocida | [evaluar.py](evaluar.py) + [casos_golden.json](casos_golden.json) |
| LLM como juez | Lo subjetivo (claridad de la documentación) con una rúbrica | `SISTEMA_JUEZ` en [evaluar.py](evaluar.py) |
| Quality gate | Si las métricas bajan del umbral, CI falla | `PASO 5` + [.github/workflows/lab8-ci.yml](../../../.github/workflows/lab8-ci.yml) |

Métricas: **recall** de tipos de regla y de construcciones SAS (¿encontró lo que debía?),
**estado correcto** (¿aprobó solo lo que debía?), intentos, costo y puntaje del juez.

**Cuidado con el LLM como juez**: tiene sesgos (prefiere textos largos, a veces su propio estilo).
Úsalo solo para lo que no se puede medir, con rúbrica concreta, y valida de vez en cuando contra
calificaciones humanas.

## Para la entrevista

- *"¿Cómo pruebas un sistema no determinista?"* → separar lo determinista (tests normales) de la
  calidad del modelo (golden set con métricas y umbrales), simulador para CI, y evaluación real
  periódica o antes de cada cambio de modelo.
- *"¿Cómo monitoreas la calidad en producción?"* → mismo golden set programado + muestreo de
  casos reales revisados por humanos + tasa de `REQUIERE_REVISION` como alerta.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
