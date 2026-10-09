# EMPIEZA AQUÍ — la ruta del el curso, en orden (#1 → #26)

> Archivo generado por `scripts/ruta.py`. Para cambiar el orden, edita ese script y vuelve a correrlo.

Haz los ejercicios **en orden**: cada uno usa lo del anterior. En cada carpeta abre primero el
archivo de la columna "Abre primero", sigue sus pasos **#1, #2, #3...** y al terminar pasa al
siguiente número. Todos los comandos se escriben en una terminal abierta en `04-ia-generativa/./`,
salvo los de la parte 2.

**¿Por dónde empiezo?**
- Nunca he programado en Python → empieza en **#1**.
- Sé Python pero no IA → empieza en **#6**.
- Sé los fundamentos de IA y quiero Google Cloud → empieza en **#15**.

**Antes del #1:** instala Python 3.12 y VS Code (ver [parte0_python/README.md](01-python-for-ai/README.md)).
**Antes del #15:** crea el entorno de la parte 2 (ver el paso #1 de
[parte2_gcp/10_setup_gcp/INSTRUCCIONES.md](04-vertex-ai-projects/10_setup_gcp/INSTRUCCIONES.md)). Todo funciona gratis en modo simulado;
conectar a Google Cloud es opcional ([docs/CONECTAR_GCP.md](docs/gcp-connect.md)).

### Parte 0 — Python para IA

| ✔ | # | Ejercicio | Abre primero | Corre | Tiempo |
|---|---|---|---|---|---|
| ☐ | **#1** | Tu primer script | [parte0_python/01_primer_script/INSTRUCCIONES.md](01-python-for-ai/01_primer_script/INSTRUCCIONES.md) | `python parte0_python/01_primer_script/ejercicio.py` | 30 min |
| ☐ | **#2** | Listas y diccionarios | [parte0_python/02_listas_y_diccionarios/INSTRUCCIONES.md](01-python-for-ai/02_listas_y_diccionarios/INSTRUCCIONES.md) | `python parte0_python/02_listas_y_diccionarios/ejercicio.py` | 40 min |
| ☐ | **#3** | Funciones | [parte0_python/03_funciones/INSTRUCCIONES.md](01-python-for-ai/03_funciones/INSTRUCCIONES.md) | `python parte0_python/03_funciones/ejercicio.py` | 40 min |
| ☐ | **#4** | Archivos, JSON y errores | [parte0_python/04_archivos_json_errores/INSTRUCCIONES.md](01-python-for-ai/04_archivos_json_errores/INSTRUCCIONES.md) | `python parte0_python/04_archivos_json_errores/ejercicio.py` | 40 min |
| ☐ | **#5** | Clases y tipos | [parte0_python/05_clases_y_tipos/INSTRUCCIONES.md](01-python-for-ai/05_clases_y_tipos/INSTRUCCIONES.md) | `python parte0_python/05_clases_y_tipos/ejercicio.py` | 40 min |

### Parte 1 — Fundamentos de IA

| ✔ | # | Ejercicio | Abre primero | Corre | Tiempo |
|---|---|---|---|---|---|
| ☐ | **#6** | Reglas vs. aprendizaje | [parte1_fundamentos/01_reglas_vs_aprendizaje/README.md](02-ai-fundamentals/01_reglas_vs_aprendizaje/README.md) | `python parte1_fundamentos/01_reglas_vs_aprendizaje/spam.py` | 10 min |
| ☐ | **#7** | Aprender = ajustar números | [parte1_fundamentos/02_aprender_es_ajustar_numeros/README.md](02-ai-fundamentals/02_aprender_es_ajustar_numeros/README.md) | `python parte1_fundamentos/02_aprender_es_ajustar_numeros/regresion.py` | 15 min |
| ☐ | **#8** | Una neurona | [parte1_fundamentos/03_una_neurona/README.md](02-ai-fundamentals/03_una_neurona/README.md) | `python parte1_fundamentos/03_una_neurona/perceptron.py` | 10 min |
| ☐ | **#9** | Red neuronal | [parte1_fundamentos/04_red_neuronal/README.md](02-ai-fundamentals/04_red_neuronal/README.md) | `python parte1_fundamentos/04_red_neuronal/red_xor.py` | 20 min |
| ☐ | **#10** | Tokens | [parte1_fundamentos/05_tokens/README.md](02-ai-fundamentals/05_tokens/README.md) | `python parte1_fundamentos/05_tokens/tokens.py` | 15 min |
| ☐ | **#11** | Embeddings | [parte1_fundamentos/06_embeddings/README.md](02-ai-fundamentals/06_embeddings/README.md) | `python parte1_fundamentos/06_embeddings/embeddings.py` | 15 min |
| ☐ | **#12** | Siguiente palabra | [parte1_fundamentos/07_siguiente_palabra/README.md](02-ai-fundamentals/07_siguiente_palabra/README.md) | `python parte1_fundamentos/07_siguiente_palabra/bigramas.py` | 15 min |
| ☐ | **#13** | Temperatura | [parte1_fundamentos/08_temperatura/README.md](02-ai-fundamentals/08_temperatura/README.md) | `python parte1_fundamentos/08_temperatura/temperatura.py` | 10 min |
| ☐ | **#14** | Mini RAG | [parte1_fundamentos/09_mini_rag/README.md](02-ai-fundamentals/09_mini_rag/README.md) | `python parte1_fundamentos/09_mini_rag/mini_rag.py` | 25 min |

### Parte 2 — IA en Google Cloud (los comandos se corren desde `parte2_gcp/`)

| ✔ | # | Ejercicio | Abre primero | Corre | Tiempo |
|---|---|---|---|---|---|
| ☐ | **#15** | Preparar el entorno | [parte2_gcp/10_setup_gcp/README.md](04-vertex-ai-projects/10_setup_gcp/README.md) | `python 10_setup_gcp/verificar_entorno.py` | 30 min |
| ☐ | **#16** | Gemini con el SDK | [parte2_gcp/11_gemini_sdk/README.md](04-vertex-ai-projects/11_gemini_sdk/README.md) | `python 11_gemini_sdk/hola_gemini.py` | 20 min |
| ☐ | **#17** | Salida estructurada | [parte2_gcp/12_salida_estructurada/README.md](04-vertex-ai-projects/12_salida_estructurada/README.md) | `python 12_salida_estructurada/extraer_reglas.py` | 30 min |
| ☐ | **#18** | RAG con embeddings | [parte2_gcp/13_embeddings_rag/README.md](04-vertex-ai-projects/13_embeddings_rag/README.md) | `python 13_embeddings_rag/rag_sas.py` | 40 min |
| ☐ | **#19** | Agente con herramientas | [parte2_gcp/14_agente_herramientas/README.md](04-vertex-ai-projects/14_agente_herramientas/README.md) | `python 14_agente_herramientas/agente.py` | 40 min |
| ☐ | **#20** | Multi-agente SAS → Python | [parte2_gcp/15_multi_agente/README.md](04-vertex-ai-projects/15_multi_agente/README.md) | `python 15_multi_agente/migrar.py` | 60 min |
| ☐ | **#21** | Evaluación y quality gate | [parte2_gcp/16_evaluacion/README.md](04-vertex-ai-projects/16_evaluacion/README.md) | `python 16_evaluacion/evaluar.py` | 40 min |
| ☐ | **#22** | BigQuery | [parte2_gcp/17_bigquery/README.md](04-vertex-ai-projects/17_bigquery/README.md) | `python 17_bigquery/sas_a_bigquery.py` | 40 min |
| ☐ | **#23** | Cloud Functions + Storage | [parte2_gcp/18_cloud_functions_storage/README.md](04-vertex-ai-projects/18_cloud_functions_storage/README.md) | `python 18_cloud_functions_storage/probar_local.py` | 30 min |
| ☐ | **#24** | API en Cloud Run | [parte2_gcp/19_cloud_run_api/README.md](04-vertex-ai-projects/19_cloud_run_api/README.md) | `uvicorn --app-dir 19_cloud_run_api app:app --port 8080` | 40 min |
| ☐ | **#25** | Dataflow y Composer | [parte2_gcp/20_composer_dataflow/README.md](04-vertex-ai-projects/20_composer_dataflow/README.md) | `python 20_composer_dataflow/pipeline_ventas_beam.py` | 40 min |
| ☐ | **#26** | Monitoreo y gobernanza | [parte2_gcp/21_monitoreo_gobernanza/README.md](04-vertex-ai-projects/21_monitoreo_gobernanza/README.md) | `python 21_monitoreo_gobernanza/reporte_costos.py` | 30 min |

## Cuando termines

- Preparación de entrevista: [docs/GUIA_ENTREVISTA.md](docs/interview-guide.md)
- Probar todo en GCP real: [docs/COMO_PROBAR_TODO.md](docs/testing-on-gcp.md)
- Costos: [docs/COSTOS_GCP.pdf](docs/gcp-costs.pdf)
