# 19 — Instrucciones

## Paso 1 — Correr la API local (simulado)

```bash
uvicorn --app-dir 19_cloud_run_api app:app --reload --port 8080
```

Abre <http://localhost:8080/docs> → `POST /migrar` → *Try it out* → pega en `codigo_sas` el
contenido de `comun/sas/ventas.sas` (como texto con `\n`) → *Execute*. O con curl desde otra terminal:

```bash
python -c "import json;print(json.dumps({'programa':'ventas.sas','codigo_sas':open('comun/sas/ventas.sas',encoding='utf-8').read()}))" > /tmp/peticion.json
curl -s -X POST localhost:8080/migrar -H "Content-Type: application/json" -d @/tmp/peticion.json | python -m json.tool
```

## Paso 2 — Probar el contenedor local (requiere Docker Desktop encendido)

```bash
bash 19_cloud_run_api/preparar_build.sh
docker build -t migrador-sas 19_cloud_run_api/build
docker run --rm -p 8080:8080 -e MODO=simulado migrador-sas
```

Si funciona en Docker, funciona en Cloud Run (es el mismo contenedor).

## Paso 3 — Desplegar (real)

```bash
export GCP_PROJECT_ID=tu-proyecto
bash 19_cloud_run_api/desplegar.sh          # 3-5 min la primera vez (Cloud Build construye la imagen)
URL=$(gcloud run services describe migrador-sas --region=us-central1 --format='value(status.url)')
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $URL/salud
curl -X POST $URL/migrar -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     -H "Content-Type: application/json" -d @/tmp/peticion.json
```

## Paso 4 — Limpiar

```bash
gcloud run services delete migrador-sas --region=us-central1
```

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `403 Forbidden` al llamar | Sin identity token o sin `run.invoker` | Header `Authorization: Bearer $(gcloud auth print-identity-token)`; tu usuario con rol **Cloud Run Invoker** |
| `422 Unprocessable Entity` | El JSON no cumple el modelo (p. ej. `codigo_sas` muy corto) | Lee `detail` en la respuesta |
| `502` con "Falló la migración" | Error dentro del orquestador | `gcloud run services logs read migrador-sas --region=us-central1` |
| `Container failed to start ... PORT` | La app no escucha en `$PORT` | El `CMD` del Dockerfile ya lo usa; no lo cambies a un puerto fijo |
| Build falla por permisos | Cuenta de Cloud Build sin roles | Ver tabla del [lab 18](../18_cloud_functions_storage/INSTRUCCIONES.md#si-algo-falla) |
| `ModuleNotFoundError: comun` en el contenedor | Construiste sin `preparar_build.sh` | Construye desde `build/` |
| Primera petición lenta | Arranque en frío (escala desde 0) | Normal; `--min-instances=1` lo evita pero cobra 24/7 |
| `docker: error during connect` | Docker Desktop apagado | Ábrelo y espera a que diga *running* |

## Retos

1. Agrega `GET /programas` que liste los `.sas` de `comun/sas/`.
2. Agrega un test en [tests/test_flujos.py](../tests/test_flujos.py) para ese endpoint.
