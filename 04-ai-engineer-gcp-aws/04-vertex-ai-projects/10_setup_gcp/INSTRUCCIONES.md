# 10 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #15 de 26** · [← #14 Mini RAG](../../02-ai-fundamentals/09_mini_rag/README.md) · [#16 Gemini con el SDK →](../11_gemini_sdk/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

Todos los comandos de la parte 2 se corren **desde `04-vertex-ai-projects/`**.

## Paso #1 — Entorno de Python (una sola vez)

```bash
cd 04-vertex-ai-projects
python -m venv .venv
source .venv/Scripts/activate      # Git Bash en Windows | PowerShell: .venv\Scripts\Activate.ps1 | Mac/Linux: .venv/bin/activate
pip install -r requirements.txt
```

¿Sin Python? Con `uv`: `uv venv --python 3.12 .venv` y `uv pip install -r requirements.txt`.

## Paso #2 — Modo simulado (gratis)

```bash
python 10_setup_gcp/verificar_entorno.py
```

Debes ver `[ OK ]` en Python y paquetes, y un `[AVISO]` por no tener `.env` (normal).
Con eso ya puedes hacer los ejercicios 11–21 en simulado.

## Paso #3 — Modo real

1. Sigue [docs/gcp-connect.md](../../docs/gcp-connect.md) (proyecto, facturación, ADC, Terraform).
2. `cp .env.example .env` y edita `MODO=real` y `GCP_PROJECT_ID`.
3. `python 10_setup_gcp/verificar_entorno.py` → hace una llamada real y barata a Gemini y a embeddings.

## Qué observar

- El orden del checklist es el orden en que suelen fallar las cosas.
- En real verás tokens y costo de la llamada de prueba (fracciones de centavo).

## Si algo falla

| Mensaje | Causa | Solución |
|---|---|---|
| `No module named 'google'` | No activaste el `.venv` o no instalaste | Activa el entorno y `pip install -r requirements.txt` |
| `Falta GCP_PROJECT_ID` | `.env` sin editar | Pon tu ID: `gcloud config get-value project` |
| `DefaultCredentialsError` | Sin ADC | `gcloud auth application-default login` |
| `403 PERMISSION_DENIED ... aiplatform.googleapis.com has not been used` | API apagada | `gcloud services enable aiplatform.googleapis.com` (o `terraform apply`) |
| `403 ... Permission 'aiplatform.endpoints.predict' denied` | Tu usuario no tiene rol | Rol **Vertex AI User** en IAM |
| `403 ... billing` | Proyecto sin facturación | `gcloud billing projects link ...` |
| `404 ... Publisher Model ... not found` | Modelo no existe en esa región o ID viejo | Cambia `GEMINI_MODEL` o `GCP_REGION_MODELOS` (`global` ↔ `us-central1`); revisa Model Garden |
| `429 RESOURCE_EXHAUSTED` | Cuota por minuto | Espera; el código ya reintenta con backoff; pide aumento de cuota |
| Advertencia sobre "quota project" | ADC sin proyecto de cuota | `gcloud auth application-default set-quota-project TU_PROYECTO` |
| Rutas raras / `ImportError` en Windows con carpetas muy profundas | Límite de 260 caracteres en rutas | Crea el `.venv` en una ruta corta o habilita *long paths* en Windows |

## Retos

1. Pon un modelo inexistente en `GEMINI_MODEL` y observa el `[FALLA]` y la pista.
2. Lee `_con_reintentos` en [comun/llm.py](../comun/llm.py): ¿por qué NO reintenta un 400?
