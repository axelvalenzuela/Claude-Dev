# Guía para la 2ª entrevista — Senior AI Engineer (migración SAS → Python/GCP)

Cómo usar esta guía: para cada punto de la vacante, corre el lab indicado, lee su
`README.md` y practica las preguntas **en voz alta** con tus palabras. Las respuestas de
aquí son esqueletos, no guiones para memorizar.

## 1. Mapa: vacante → micro lab

| Lo que pide la vacante | Dónde lo practicas |
|---|---|
| LLMs, Generative AI | parte 1 (05–08), lab 11 |
| RAG, contextual retrieval, vector databases | parte 1 (06, 09), lab 13, lab 17 (`VECTOR_SEARCH`) |
| AI Agents, Agentic AI frameworks | lab 14 (tools), lab 15 (ADK) |
| Multi-agent workflows, agent orchestration, agent-to-agent | lab 15 |
| SAS code analysis, business rule extraction | labs 12 y 15 (analista) |
| Code generation SAS → Python / BigQuery SQL | lab 15 (Python), lab 17 (SQL) |
| Dataflow Pipelines, Cloud Composer workflows | lab 20 |
| Validation, testing & QA frameworks for AI output | labs 15 (validador), 16 (evaluación + CI) |
| Monitor model performance, governance | lab 21, `.github/workflows/lab8-ci.yml` |
| Vertex AI, Gemini | labs 10–16 |
| BigQuery, Cloud Storage, Cloud Functions, Cloud Run | labs 17, 18, 19 + `infra/` (Terraform) |
| Documentation automation | lab 15 (documentador) |
| Software best practices, REST APIs | lab 19, tests, CI, Terraform, este repo |
| LookML | ver pregunta 12 abajo (no hay lab: se explica) |

## 2. Cuenta tu historia en 2 minutos (arquitectura)

```
            ┌────────────── Cloud Composer (DAG por lotes, reintentos, calendario) ──────────────┐
 .sas ──> Cloud Storage ──evento──> Cloud Function (análisis rápido)                              │
                     │                                                                            ▼
                     └──> Cloud Run: API /migrar ──> Orquestador multi-agente ──> BigQuery (resultados, auditoría)
                                                     │
                     Analista (Gemini, JSON) ──> Convertidor (Gemini) <──> Validador (código, NO LLM)
                                                     │                        ejecuta + reconcilia vs salida SAS
                                                     └──> Documentador (Gemini) ──> Markdown para negocio/auditoría
                     RAG: conocimiento de equivalencias SAS↔Python en BigQuery VECTOR_SEARCH
```

Frase clave: **"el LLM propone, una verificación determinista decide"**. La confianza en una
migración viene de reconciliar números contra SAS, no de que el código "se vea bien".

## 3. Preguntas probables y esqueleto de respuesta

**1. ¿Cómo sabes que el código que generó el LLM es correcto?**
Reconciliación: corro SAS una última vez para guardar entradas y salidas (golden data), ejecuto
el Python generado con las mismas entradas y comparo fila por fila con tolerancia numérica
(lab 15, `comun/validacion.py`). Si falla, el error concreto vuelve al convertidor (ciclo de
autocorrección, máximo N intentos). Sin datos de prueba no hay aprobación automática.

**2. ¿Qué haces si el agente se equivoca siempre en el mismo tipo de programa?**
Lo veo en la evaluación (lab 16): baja el recall en ese tipo. Opciones en orden de costo:
(1) mejorar instrucciones/ejemplos del agente para ese patrón, (2) agregar conocimiento vía RAG
(equivalencias), (3) un modelo más capaz solo para ese rol, (4) preprocesar (p. ej. expandir
macros antes de convertir). Cada cambio se mide contra el golden set; si no mejora, no se mergea.

**3. ¿Por qué varios agentes y no un solo prompt?**
Responsabilidad única: cada uno se prueba, mide y mejora aparte; puedo usar modelos distintos
por rol (barato para documentar, potente para convertir); sé en qué paso falló. El validador ni
siquiera es un LLM.

**4. ¿Cómo orquestas agentes? ¿Framework o a mano?**
Mostré ambos (lab 15): orquestador explícito en Python (control total, fácil de depurar) y
Google ADK con `SequentialAgent` + `LoopAgent`. Un framework aporta sesiones, estado, trazas,
despliegue (Agent Engine) y protocolos como A2A (agent-to-agent) cuando los agentes viven en
servicios distintos. Elijo según cuánto control y observabilidad necesito.

**5. ¿Cómo funciona RAG y cuándo NO lo usarías?**
Fragmentar → embeber (RETRIEVAL_DOCUMENT) → al preguntar, embeber (RETRIEVAL_QUERY), top-k por
coseno, pegar al prompt con la instrucción "solo usa el CONTEXTO". No lo uso si el conocimiento
cabe entero en el contexto y cambia poco (más simple pegarlo, con context caching), o si lo que
quiero cambiar es *comportamiento* (eso es prompt/fine-tuning).

**6. ¿Qué base vectorial usarías?**
Para empezar, BigQuery `VECTOR_SEARCH`: sin servidores extra, pagas por consulta y los datos ya
están ahí. AlloyDB/pgvector si necesito transacciones y baja latencia. Vertex AI Vector Search
para gran escala y latencia de milisegundos, sabiendo que cobra por nodo encendido 24/7.

**7. ¿Cómo evitas alucinaciones?**
Instrucción de "si no está en el contexto, di que no sabes", umbral de similitud (no mandar
contexto irrelevante), salida estructurada validada con Pydantic, pedir el fragmento SAS de
origen de cada regla (trazabilidad) y, sobre todo, validación determinista.

**8. ¿Cómo controlas costos?**
Medir tokens por rol (lab 21), modelo barato por defecto y caro solo donde hace falta, límites
de intentos/pasos, context caching para instrucciones repetidas, Batch API (-50 %) para lotes,
dry run en BigQuery antes de ejecutar, `max-instances` en Cloud Run, presupuesto con alertas.
Proyección en [COSTOS_GCP.pdf](COSTOS_GCP.pdf).

**9. ¿Qué pasa con datos sensibles?**
Redacción antes de enviar (lab 21), Vertex AI dentro del perímetro de GCP (sin entrenar con tus
datos), cuentas de servicio con mínimo privilegio (`infra/iam.tf`), sin llaves JSON, VPC Service
Controls y CMEK en producción, auditoría en BigQuery.

**10. ¿Es seguro ejecutar código generado por IA?**
No por defecto. Revisión estática (AST: imports y funciones prohibidas), ejecución en proceso
aparte con timeout, y en producción en un sandbox sin red ni credenciales (Cloud Run Job
aislado / gVisor).

**11. ¿Cómo lo llevas a producción?**
Contenedor en Cloud Run con autenticación, Terraform para la infraestructura, CI con tests +
quality gate de evaluación, logs estructurados, versionado de prompts junto al código, y
despliegue gradual (traffic splitting de Cloud Run) comparando métricas.

**12. ¿Y LookML?**
LookML es la capa semántica de Looker: define dimensiones y medidas sobre tablas de BigQuery.
En una migración, los reportes de SAS (PROC REPORT/TABULATE) se vuelven vistas LookML sobre las
tablas migradas. Un agente puede generar el `view` a partir del esquema de la tabla y de las
reglas extraídas, y se valida con el LookML Validator y comparando totales contra SAS.

**13. Cuando falla una Cloud Function con evento de Storage, ¿qué revisas?**
Logs (`gcloud functions logs read`), que el evento llegue (permiso `pubsub.publisher` del agente
de servicio de Storage, lo da `infra/iam.tf`), que la cuenta del trigger tenga `run.invoker`, el
filtro de carpeta (evitar ciclos) y el timeout.

**14. ¿Dataflow o BigQuery?**
BigQuery si la transformación se expresa en SQL (la mayoría de DATA steps y PROC SQL). Dataflow
para streaming, lógica fila a fila compleja o muchas fuentes/destinos. Composer orquesta ambos.

## 4. "Algo está mal": diagnóstico rápido

| Síntoma | Primera sospecha | Dónde lo practicaste |
|---|---|---|
| 403 PERMISSION_DENIED | API no habilitada o falta rol en la cuenta | lab 10 |
| 404 model not found | ID de modelo o región (Gemini 3 usa `global`) | lab 10 |
| 429 RESOURCE_EXHAUSTED | Cuota: reintentos con backoff, pedir cuota, Batch | `comun/llm.py` |
| JSON que no valida | Falta `response_schema` o esquema ambiguo | lab 12 |
| RAG responde con otro tema | Umbral bajo, chunks malos o `task_type` mal | lab 13 |
| El agente se cicla | Descripción de herramientas vaga; límite de pasos | lab 14 |
| La migración nunca aprueba | Leer la retroalimentación del validador: ¿regla, tipo de dato, redondeo? | lab 15 |
| Métricas bajan tras cambiar prompt | Quality gate en CI lo bloquea; comparar casos | lab 16 |
| Consulta de BigQuery cara | Dry run; particiones; no `SELECT *` | lab 17 |
| La Function se dispara sola sin parar | Escribe en la carpeta que la dispara | lab 18 |
| Cloud Run 403 al llamarlo | Falta identity token o rol `run.invoker` | lab 19 |
| Costo sube sin explicación | Reporte por rol/modelo; logs; presupuesto | lab 21 |

## 5. Dato actual que suma puntos

`gemini-2.5-flash` (el que usa lab7) se retira alrededor del 16–20 de octubre de 2026. Los
labs usan `gemini-3.1-flash-lite` por defecto y el modelo se configura por variable de entorno,
así que cambiarlo no requiere tocar código. Mencionar que tienes un plan para retiros de
modelos (configuración + evaluación automática antes de cambiar) demuestra experiencia de
producción.
