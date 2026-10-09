# FAQ — Agentes del Programa Helios

**¿Cuántos agentes tiene el pipeline y qué hace cada uno?**
Cinco: Extractor (lee SAS y extrae reglas de negocio y linaje de datos),
Conversor (genera el código Python/BigQuery equivalente), Validador
(reconcilia contra el dataset dorado), Documentador (genera README y ADR
del módulo migrado), y Consulta (responde preguntas sobre toda esta
documentación vía RAG — es el que se implementa en este laboratorio).

**¿Los agentes se comunican entre sí directamente?**
No. Cada agente es un servicio Cloud Run independiente sin estado propio;
Cloud Composer orquesta el orden y pasa el resultado de un agente como
entrada del siguiente a través de un bucket de artefactos en Cloud
Storage (`gs://acme-helios-artifacts/runs/<job_id>/`). Ningún agente llama
directamente a otro por HTTP.

**¿Qué pasa si el Agente Conversor no encuentra un equivalente claro en
GCP para una función SAS?**
Marca el módulo como `requiere-revision-manual` en el reporte del run y
detiene ese job específico (no bloquea el resto del batch). Un ingeniero
humano decide el equivalente y lo documenta como un nuevo renglón en la
tabla de mapeo de `02_arquitectura_gcp.md` para que futuros runs lo
reutilicen.

**¿Con qué modelo corren los agentes?**
Todos usan Gemini a través de Vertex AI en el proyecto
`acme-helios-dev`. El Agente Extractor y el Conversor usan el modelo de
mayor capacidad de razonamiento disponible (más lento, más caro, porque
trabajan con código); el Agente de Consulta y el Documentador usan el
modelo rápido, porque sus respuestas son más cortas y el volumen de
preguntas es alto.

**¿Cómo se mide el éxito del programa?**
Porcentaje de jobs con veredicto PASA en el primer intento (objetivo:
70% para fin de 2026), y tiempo promedio desde "job en cola" hasta
"fusionado a main" (objetivo: menos de 5 días hábiles por job).
