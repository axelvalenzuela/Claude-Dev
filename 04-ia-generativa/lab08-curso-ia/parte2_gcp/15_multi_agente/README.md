# 15 — Flujo multi-agente: migrar SAS → Python con autocorrección

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #20 de 26** · [← #19 Agente con herramientas](../14_agente_herramientas/README.md) · [#21 Evaluación y quality gate →](../16_evaluacion/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** el núcleo de la vacante: varios agentes especializados, orquestados,
con un validador determinista que hace que el sistema se corrija solo.

## Arquitectura

```
                 ┌────────────────────── retroalimentación (errores concretos) ─────────────────────┐
                 ▼                                                                                   │
SAS ─> ANALISTA ─> CONVERTIDOR ─> VALIDADOR ──ok──> DOCUMENTADOR ─> APROBADO                          │
      (Gemini,     (Gemini,        (código Python: ─falla──────────────────────────────────────────┘
       JSON)        Python)         guardrails + ejecutar + reconciliar vs salida de SAS)
                                     └─ tras MAX_INTENTOS ─> REQUIERE_REVISION (humano)
```

| Pieza | Archivo | Es LLM |
|---|---|---|
| Analista, Convertidor, Documentador | [comun/agentes.py](../comun/agentes.py) | Sí |
| Validador | [comun/validacion.py](../comun/validacion.py) + [comun/guardrails.py](../comun/guardrails.py) | **No** |
| Orquestador | [comun/orquestador.py](../comun/orquestador.py) | No |
| Punto de entrada | [migrar.py](migrar.py) | — |
| Mismo flujo con Google ADK | [adk_migracion/agent.py](adk_migracion/agent.py) | Sí (framework) |

## Decisiones de diseño (lo que te van a preguntar)

1. **El validador no es un LLM.** Que dos LLMs estén de acuerdo no prueba nada; que los números
   coincidan con SAS, sí.
2. **La retroalimentación es concreta**: "(CENTRO, ALTA) num_ventas: se esperaba 3, se obtuvo 1",
   no "está mal". Eso es lo que permite corregir.
3. **Límite de intentos** y estado `REQUIERE_REVISION`: ni gasto infinito ni aprobaciones falsas.
4. **Sin datos de prueba no hay aprobación** (`clientes.sas`): human-in-the-loop.
5. **Contrato explícito** para el código generado: `def transformar(df) -> DataFrame`, solo pandas/numpy,
   columnas de salida exactas. Sin contrato, no se puede validar automáticamente.
6. **Un modelo por rol es posible**: `generar(..., modelo=...)`.

## Orquestación a mano vs framework (ADK)

| | [comun/orquestador.py](../comun/orquestador.py) | [adk_migracion/](adk_migracion/) (Google ADK) |
|---|---|---|
| Flujo | `for` + `if` explícitos | `SequentialAgent` + `LoopAgent` |
| Estado compartido | variables locales | `output_key` → estado de sesión (`{analisis}` en instrucciones) |
| Salir del ciclo | `break` | la herramienta pone `tool_context.actions.escalate = True` |
| Ventajas | control total, depuración trivial, modo simulado | UI de trazas (`adk web`), sesiones, despliegue en Agent Engine, A2A |

**A2A (Agent2Agent)**: protocolo abierto para que agentes en *servicios distintos* se descubran y
se deleguen tareas. Aquí todos viven en un proceso; si el Validador fuera un servicio de otro equipo,
A2A sería la forma estándar de hablarle.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
