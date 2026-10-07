# Micro lab 14 (GCP · GenAI): Agente con Google ADK (Agent Development Kit) y herramientas

> **Objetivo:** Construir un **agente** que razona, elige herramientas, mantiene memoria de sesión y escribe en sistemas reales, con el framework oficial de Google (**ADK**), listo para Cloud Run o Vertex AI Agent Engine.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~6 min · **Costo si queda encendido:** Por token

**Prerrequisitos**

- Lab 00 (`build_service_account`)

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
cp microlabs/14-genai-agent-adk/terraform.tfvars.example microlabs/14-genai-agent-adk/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `invoker_members` | `["user:tu@correo"]` |
| `build_service_account` | output del lab 00 |
| `sample_orders` | opcional, pedidos de prueba |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  14-genai-agent-adk
bash scripts/lab.sh plan  14-genai-agent-adk   # revisa qué se crea
bash scripts/lab.sh apply 14-genai-agent-adk
```

**3. Después del apply**

- Conversa: `curl -X POST <agent_url> -H "Authorization: Bearer $(gcloud auth print-identity-token)" -d '{"message":"¿Dónde está mi pedido PED-1001?","session":"s1"}'`
- Local con UI de depuración de ADK: `pip install google-adk && adk web` dentro de `src/` (muestra cada llamada a herramienta)

**4. Verifica**

```bash
bash scripts/lab.sh test 14-genai-agent-adk   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 14-genai-agent-adk
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| src/agent/main.py → funciones `consultar_pedido`, `crear_ticket`... | Herramientas del agente (docstring = descripción para el modelo) | Tu dominio |
| src/agent/main.py → `Agent(instruction=...)` | Comportamiento y límites del agente | Siempre |
| src/agent/main.py → `InMemorySessionService` | Cambiar por `VertexAiSessionService` o una BD | Memoria persistente en producción |
| variables.tf → `sample_orders` | Datos de prueba | Para tus pruebas |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Cliente ──ID token──► Cloud Run function (ADK Runner)
                         │ Agent(model=gemini-2.5-flash, instruction, tools=[...])
                         │ SessionService (memoria por session_id)
                         ▼
             Gemini decide → function call → herramienta Python → resultado → Gemini → ... → respuesta final
                         │
     consultar_pedido ─► Firestore pedidos      crear_ticket ─► Firestore tickets      politica_devoluciones (local)
```

## Conceptos clave (nivel senior)

| Concepto | Lo que debes saber explicar |
|---|---|
| Agente vs chatbot | Un agente decide acciones (herramientas) en un bucle razonar → actuar → observar hasta cumplir el objetivo. |
| Herramientas | Funciones con type hints y docstring: el docstring es lo que el modelo lee para decidir cuándo usarlas. Describe cuándo NO usarlas. |
| Sesiones y memoria | `SessionService` guarda el historial (InMemory para el lab; `VertexAiSessionService` o una BD en producción). Memoria de largo plazo: `MemoryService`. |
| Multi-agente | ADK permite sub-agentes (`sub_agents=[...]`) y agentes de flujo (`SequentialAgent`, `ParallelAgent`, `LoopAgent`). |
| Agent Engine | Runtime administrado en Vertex AI: `adk deploy agent_engine` publica el agente con sesiones, escalado y trazas. |
| MCP y A2A | MCP conecta agentes con herramientas externas (`MCPToolset`); A2A es el protocolo para que agentes de distintos sistemas colaboren. |
| Riesgos | Herramientas de escritura requieren confirmación, validación de argumentos, mínimo privilegio (IAM condicionado) y límites de iteraciones. |

## Recursos de Terraform y código

| Recurso / archivo | Propósito |
|---|---|
| `src/agent/main.py` | Agent, herramientas, Runner y handler HTTP |
| `google_firestore_database.store` + `google_firestore_document.orders` | Datos que consultan las herramientas |
| `google_project_iam_member.agent_firestore` | IAM condicionado a una sola base |
| `module.agent_fn` | 1 GiB, 120 s, concurrencia 4 |

## Comandos útiles

```bash
pip install google-adk && adk web          # UI local para depurar eventos y llamadas
adk run src/agent                           # chat en terminal
adk deploy agent_engine --project <p> --region us-central1 src/agent   # runtime administrado
gcloud firestore documents list ... (o consola) para ver los tickets creados
```

## Prueba automatizada (`scripts/smoke-test.sh`)

Pregunta por PED-1003 → llama `consultar_pedido` y responde "retrasado"; pregunta por devolución → usa la memoria (categoría hogar) y llama `politica_devoluciones` (15 días); PED-9999 → "no existe"; sin número de pedido → lo pide sin llamar herramientas.

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| La memoria no persiste entre llamadas | `InMemorySessionService` vive en cada instancia; con varias instancias usa `VertexAiSessionService`. |
| Timeout en la primera llamada | Arranque en frío al importar ADK; sube `min_instances` o `timeout_seconds`. |
| El agente inventa datos | Refuerza la `instruction` y que las herramientas devuelvan errores explícitos. |

## Costo

Por tokens (cada paso del agente es una llamada al modelo) + Firestore por operación.
