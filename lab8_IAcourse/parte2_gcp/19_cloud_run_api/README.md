# 19 — API REST del migrador en Cloud Run

**Qué aprendes:** exponer el flujo multi-agente como un servicio REST en contenedor,
desplegado en Cloud Run con autenticación, límites y escalado a cero.

## Conceptos

```
cliente (Composer, otra app, curl) ──HTTPS + identity token──> Cloud Run: migrador-sas
                                                                 FastAPI (app.py)
                                                                 ├─ GET  /salud
                                                                 ├─ POST /migrar ─> redactar PII ─> orquestador (lab 15)
                                                                 └─ GET  /docs  (Swagger automático)
```

- **Contenedor** ([Dockerfile](Dockerfile)): imagen slim, dependencias en capa aparte (builds rápidos),
  usuario no-root, `PORT` desde el entorno.
- **Cloud Run**: escala de 0 a N instancias; sin tráfico = 0 USD. `max-instances` = techo de gasto.
- **`--no-allow-unauthenticated`**: solo quien tenga `roles/run.invoker` puede llamar. Una API que
  gasta tokens nunca debe estar abierta.
- **Validación de entrada** con Pydantic: `max_length` evita que te manden 50 MB y te hagan gastar.
- **Contrato de respuesta** (`response_model`): la API documenta y garantiza su forma.

## Archivos

| Archivo | Qué hace |
|---|---|
| [app.py](app.py) | La API FastAPI |
| [Dockerfile](Dockerfile) | Imagen para Cloud Run |
| [requirements.txt](requirements.txt) | Solo lo que usa el contenedor |
| [preparar_build.sh](preparar_build.sh) | Junta `app.py` + `comun/` en `build/` |
| [desplegar.sh](desplegar.sh) | `gcloud run deploy --source` con cuenta de servicio y límites |

## Para la entrevista

- *"¿Cómo desplegarías esto en producción?"* → Cloud Run con cuenta de servicio dedicada, sin
  acceso público, límites de instancias y tamaño de entrada, logs JSON, imagen versionada en
  Artifact Registry, Terraform, y despliegue gradual con *traffic splitting*.
- *"¿Y si una migración tarda 10 minutos?"* → no bloquear la petición HTTP: recibir, encolar
  (Pub/Sub / Cloud Tasks) y procesar en un Cloud Run Job; el cliente consulta el estado.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
