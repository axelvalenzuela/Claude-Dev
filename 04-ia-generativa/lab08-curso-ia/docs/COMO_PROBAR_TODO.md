# Cómo probar todo lo que hay en el lab 8

Tres niveles. Cada uno agrega realismo (y requisitos). Haz el nivel 1 completo antes de pasar al 2.

| Nivel | Requiere | Costo | Qué pruebas |
|---|---|---|---|
| 1. Local simulado | Python 3.10+ | 0 | Todo el flujo, tests, evaluación, Beam local |
| 2. Local contra GCP | Nivel 1 + [CONECTAR_GCP.md](CONECTAR_GCP.md) | centavos | Gemini, embeddings, BigQuery reales |
| 3. Desplegado en GCP | Nivel 2 | centavos (Composer: caro, opcional) | Cloud Functions, Cloud Run, Dataflow, Composer |

Todos los comandos se corren desde `04-ia-generativa/lab08-curso-ia/`. En Windows usa **Git Bash** (los
`.sh` son bash).

## Nivel 1 — Local, simulado, gratis

```bash
# Parte 1: sin instalar nada
for f in parte1_fundamentos/*/*.py; do python "$f"; done

# Parte 2
cd parte2_gcp
python -m venv .venv && source .venv/Scripts/activate     # macOS/Linux: .venv/bin/activate
pip install -r requirements.txt

python 10_setup_gcp/verificar_entorno.py
python 11_gemini_sdk/hola_gemini.py
python 12_salida_estructurada/extraer_reglas.py
python 13_embeddings_rag/rag_sas.py
python 14_agente_herramientas/agente.py
python 15_multi_agente/migrar.py
python 16_evaluacion/evaluar.py
python 17_bigquery/sas_a_bigquery.py
python 18_cloud_functions_storage/probar_local.py
uvicorn --app-dir 19_cloud_run_api app:app --port 8080        # abre http://localhost:8080/docs ; Ctrl+C para salir
python 21_monitoreo_gobernanza/demo_guardrails.py
python 21_monitoreo_gobernanza/reporte_costos.py

pytest -v                         # 20 tests
ruff check ..                     # lint (pip install ruff)
```

Beam (lab 20) va en **otro** entorno virtual porque es pesado y choca con otras librerías:

```bash
python -m venv .venv-beam && source .venv-beam/Scripts/activate
pip install -r 20_composer_dataflow/requirements-beam.txt pydantic
python 20_composer_dataflow/pipeline_ventas_beam.py
```

Contenedor de Cloud Run en tu máquina (requiere Docker Desktop encendido):

```bash
bash 19_cloud_run_api/preparar_build.sh
docker build -t migrador-sas 19_cloud_run_api/build
docker run --rm -p 8080:8080 -e MODO=simulado migrador-sas
```

Terraform sin tocar la nube (valida sintaxis y referencias):

```bash
cd infra && terraform init -backend=false && terraform validate
```

## Nivel 2 — Local contra GCP real

1. Sigue [CONECTAR_GCP.md](CONECTAR_GCP.md) (proyecto, ADC, `terraform apply`, `.env` con `MODO=real`).
2. `python 10_setup_gcp/verificar_entorno.py` sin `[FALLA]`.
3. Corre los mismos comandos del nivel 1 (labs 11–17 y 21). Ahora responde Gemini de verdad.
4. Extras que solo existen en real:
   - `python 17_bigquery/rag_en_bigquery.py "¿cómo quito registros repetidos?"`
   - `python 21_monitoreo_gobernanza/reporte_costos.py --bigquery`
   - ADK: ver [15_multi_agente/INSTRUCCIONES.md](../parte2_gcp/15_multi_agente/INSTRUCCIONES.md#versión-con-adk)

Qué cambia al pasar a real (y es normal):
- Las respuestas varían entre corridas (los modelos no son deterministas).
- El convertidor puede acertar al primer intento o necesitar 3; si agota los intentos, el estado es `REQUIERE_REVISION` (por diseño).
- `16_evaluacion/evaluar.py` puede fallar el quality gate: es justo para eso. Lee qué métrica bajó.

## Nivel 3 — Desplegado en GCP

```bash
export GCP_PROJECT_ID=tu-proyecto
bash parte2_gcp/18_cloud_functions_storage/desplegar.sh   # luego sube un .sas (el script te dice cómo)
bash parte2_gcp/19_cloud_run_api/desplegar.sh             # luego curl con identity token
```

Dataflow y Composer: ver [20_composer_dataflow/INSTRUCCIONES.md](../parte2_gcp/20_composer_dataflow/INSTRUCCIONES.md).
**Composer cuesta ~13 USD por día**; créalo solo si quieres verlo y destrúyelo el mismo día.

## CI: la prueba automática

`.github/workflows/lab8-ci.yml` corre el nivel 1 completo (lint, parte 1, pytest,
quality gate) y `terraform validate` en cada push que toque `04-ia-generativa/lab08-curso-ia/`. Revisa la
pestaña **Actions** de GitHub después de subir cambios.
