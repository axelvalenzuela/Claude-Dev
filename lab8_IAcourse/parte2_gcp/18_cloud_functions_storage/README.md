# 18 — Cloud Storage + Cloud Functions: IA disparada por eventos

**Qué aprendes:** arquitectura orientada a eventos: subir un archivo dispara el análisis
automáticamente, sin servidores encendidos esperando.

## Conceptos

```
gcloud storage cp ventas.sas gs://BUCKET/entrada/
        │  evento "object.finalized"
        ▼
   Eventarc ──(Pub/Sub por dentro)──> Cloud Function analizar_sas (2ª gen, corre sobre Cloud Run)
                                          │ 1. filtra: solo entrada/*.sas
                                          │ 2. lee el archivo
                                          │ 3. agente Analista (Gemini, JSON)
                                          ▼ 4. escribe
                              gs://BUCKET/resultados/ventas.json
```

- **Cloud Functions vs Cloud Run**: Function = solo el código de una función, Google arma el
  contenedor; ideal para reaccionar a eventos. Cloud Run = tu contenedor completo; ideal para APIs.
  Las Functions de 2ª gen corren *sobre* Cloud Run.
- **CloudEvent**: formato estándar del evento (`type`, `source`, `data` con `bucket` y `name`).
- **Idempotencia**: los eventos pueden llegar **más de una vez**. Procesar dos veces el mismo
  archivo debe dar el mismo resultado (aquí: sobrescribe el mismo JSON).
- **El ciclo infinito**: escribir en la carpeta que te dispara = te disparas a ti mismo sin fin.
- **Cuenta de servicio propia** con permisos mínimos (la crea Terraform).

## Archivos

| Archivo | Qué hace |
|---|---|
| [funcion/main.py](funcion/main.py) | La función (PASO 1–4). Funciona local (simulado) y desplegada |
| [probar_local.py](probar_local.py) | Arma el CloudEvent a mano y llama a la función |
| [desplegar.sh](desplegar.sh) | Empaqueta con `comun/` y despliega con `gcloud` |

## Para la entrevista

- *"¿Cuándo usas Functions, Run o Composer?"* → evento puntual → Function; API/servicio → Run;
  flujo de muchos pasos con calendario y reintentos → Composer.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
