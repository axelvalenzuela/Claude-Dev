# Instrucciones — correr local y desplegar a Cloud Run

## 0. Prerrequisitos

- Una cuenta de Google Cloud con **facturación habilitada** (Vertex AI no
  tiene capa gratuita indefinida, pero el uso de este laboratorio —
  algunas decenas de llamadas de prueba — cuesta centavos de dólar; ver
  la nota de costos al final).
- [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) instalado.
- Python 3.11 o superior.
- (Solo si vas a desplegar) un proyecto GCP donde tengas rol de Editor o
  equivalente, o alguien que pueda habilitar APIs y crear el servicio por ti.

## 1. Crear/seleccionar el proyecto GCP y habilitar la API

```bash
gcloud auth login
gcloud config set project TU_PROYECTO_ID

# La única API que este lab necesita para correr localmente:
gcloud services enable aiplatform.googleapis.com
```

Si no tienes un proyecto todavía:

```bash
gcloud projects create TU_PROYECTO_ID
gcloud billing projects link TU_PROYECTO_ID --billing-account=TU_CUENTA_DE_FACTURACION
```

(`gcloud billing accounts list` para ver tus cuentas de facturación.)

## 2. Credenciales para desarrollo local (ADC)

El SDK `google-genai` no lee una API key de este lab — usa **Application
Default Credentials** (ADC), el mecanismo estándar de autenticación de
GCP. Este comando abre el navegador, inicia sesión, y guarda un archivo
de credenciales local que el SDK encuentra automáticamente:

```bash
gcloud auth application-default login
```

No necesitas crear ni descargar ninguna llave (`.json` de service
account) para desarrollo local — eso es para cuando la app corre *fuera*
de tu máquina sin gcloud (por ejemplo, un CI). En Cloud Run tampoco hace
falta: el servicio usa su propia cuenta de servicio automáticamente (ver
paso 6).

## 3. Instalar y configurar

```bash
cd lab7
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Edita `.env` y pon tu `GCP_PROJECT_ID` real (el id, no el nombre — lo ves
con `gcloud config get-value project`).

## 4. Construir el índice vectorial (opcional — la app lo hace sola)

```bash
python -m src.ingest
```

Esto lee `data/docs/*.md`, los parte en fragmentos, llama una vez a
`text-embedding-005` con todos los fragmentos, y guarda el resultado en
`data/index/` (dos archivos: `embeddings.npy` y `chunks.json`). Deberías
ver algo como:

```
Ingesting 5 documents from .../data/docs
Split into 26 chunks, embedding in one batch call...
Index saved to .../data/index
```

Si te saltas este paso, `src/main.py` lo hace automáticamente la primera
vez que arranca el servidor (con unos segundos extra en el primer
arranque) — ver el docstring de `lifespan()` en `src/main.py`.

### Contar tokens antes de gastar cuota

```bash
python -m src.count_tokens "cual es el objetivo del programa Helios?"
```

Imprime dos cosas: el conteo de tokens de la pregunta ANTES de llamar al
modelo (gratis, `client.models.count_tokens`), y el `usage_metadata` real
que devuelve Gemini tras una llamada a `generate_content` (prompt,
respuesta y total de tokens facturados). Útil para entender cuánto pesa
un prompt, o para presupuestar costo antes de subir el volumen de
llamadas. Ver `src/count_tokens.py` y `src/gemini_client.py`.

## 5. Correr localmente y probar

```bash
uvicorn src.main:app --reload --port 8080
```

Abre `http://localhost:8080`. Prueba, en este orden:

1. Con "Usar RAG" **activado**, pregunta algo que sí esté en los
   documentos: *"¿Cuál es el umbral de reconciliación para columnas
   numéricas?"* — debería responder "0.01%" y citar
   `03_proceso_validacion.md`.
2. Con "Usar RAG" **desactivado**, haz la misma pregunta — Gemini no
   tiene forma de saberlo (el Programa Helios es inventado) y debería
   decir que no lo sabe, o dar una respuesta genérica sin ese dato
   específico.
3. Con RAG activado, pregunta algo que **no** está en los documentos
   (ej. *"¿de qué color es el logo de Acme Analytics?"*) — la instrucción
   del prompt (ver `rag_engine.SYSTEM_PROMPT`) le pide admitir que no lo
   sabe en vez de inventar.

Esta comparación es la forma más directa de *ver* qué aporta RAG, más
allá de leerlo en [CONCEPTOS.md](CONCEPTOS.md).

`GET /api/health` sirve para confirmar que el servidor está vivo sin
gastar una llamada a Vertex AI.

## 6. Desplegar a Cloud Run (manual — recomendado para entender el flujo)

Un solo comando construye la imagen (usa el `Dockerfile` del repo) **y**
la despliega:

```bash
cd lab7   # la raíz del lab, donde está el Dockerfile

gcloud run deploy lab7-rag-gemini \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=TU_PROYECTO_ID,GCP_LOCATION=us-central1
```

`--allow-unauthenticated` hace la URL pública (cualquiera con el link
puede usar el chat) — está bien para un demo personal; quítalo si
prefieres que solo tú puedas llamarlo con un token de identidad.

Por defecto, Cloud Run usa la cuenta de servicio de cómputo del proyecto,
que suele tener más permisos de los que esta app necesita. Para una
identidad mínima (recomendado, y lo que hace `infra/` en Terraform):

```bash
gcloud iam service-accounts create lab7-rag-sa \
  --display-name="Runtime SA para lab7 (RAG con Vertex AI)"

gcloud projects add-iam-policy-binding TU_PROYECTO_ID \
  --member="serviceAccount:lab7-rag-sa@TU_PROYECTO_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud run deploy lab7-rag-gemini \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account="lab7-rag-sa@TU_PROYECTO_ID.iam.gserviceaccount.com" \
  --set-env-vars GCP_PROJECT_ID=TU_PROYECTO_ID,GCP_LOCATION=us-central1
```

Al terminar, el comando imprime una URL tipo
`https://lab7-rag-gemini-xxxxx-uc.a.run.app`. Ábrela — es la misma página
que probaste en local, ahora pública. El primer request tarda un poco
más de lo normal porque el contenedor construye el índice vectorial en
frío (ver `src/main.py`).

### Alternativa: Terraform (IaC)

Si prefieres declarar esto como infraestructura versionada en vez de un
comando suelto, ver [infra/README.md](infra/README.md) — mismo
resultado, pero reproducible y con `terraform plan` mostrando qué va a
cambiar antes de aplicarlo.

## 7. Verificar el despliegue

```bash
SERVICE_URL=$(gcloud run services describe lab7-rag-gemini --region us-central1 --format='value(status.url)')

curl "$SERVICE_URL/api/health"

curl -X POST "$SERVICE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué umbral de reconciliación se usa para columnas numéricas?", "use_rag": true}'
```

## 8. Limpieza (para no seguir pagando)

```bash
gcloud run services delete lab7-rag-gemini --region us-central1

# Opcional: quitar también la cuenta de servicio y deshabilitar la API
gcloud iam service-accounts delete lab7-rag-sa@TU_PROYECTO_ID.iam.gserviceaccount.com
gcloud services disable aiplatform.googleapis.com
```

Cloud Run con `min_instances=0` (el default) no cobra nada mientras nadie
lo usa, pero mejor borrarlo cuando termines el ejercicio.

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `RuntimeError: GCP_PROJECT_ID no está configurado` | No copiaste/editaste `.env` | `cp .env.example .env` y pon tu project id real |
| `403 PERMISSION_DENIED` al llamar a Vertex AI | Tu cuenta/service account no tiene `roles/aiplatform.user`, o la API no está habilitada | `gcloud services enable aiplatform.googleapis.com` y revisa el paso 6 |
| `404` o "model not found" en `generate_content`/`embed_content` | El id de modelo en `.env` ya no existe en esa región, o cambió de nombre | Revisa los modelos disponibles en Vertex AI Model Garden para tu proyecto/región |
| Local funciona pero Cloud Run da 403 al llamar a Vertex AI | El service account del servicio no tiene el rol | Repite el `gcloud projects add-iam-policy-binding` del paso 6 con el SA correcto |
| Primer request después de desplegar tarda varios segundos | Normal: el contenedor está construyendo el índice vectorial en frío | Solo pasa una vez por contenedor frío; espera o sube `min_instance_count` en `infra/main.tf` si te molesta la latencia |
| `FileNotFoundError: No se encontraron archivos .md` al correr `python -m src.ingest` | Lo corriste desde una carpeta distinta a `lab7/` | Ejecuta los comandos desde la raíz de `lab7/`, no desde `src/` |

## Nota sobre costos

Vertex AI cobra por token, tanto para embeddings como para generación con
Gemini. El volumen de este laboratorio (5 documentos pequeños, unas
decenas de preguntas de prueba) cuesta una fracción de centavo. Cloud Run
cobra por tiempo de CPU/memoria mientras atiende requests, y $0 mientras
está inactivo con `min_instances=0`. Revisa los precios vigentes en la
consola de facturación de GCP antes de dejarlo corriendo por mucho
tiempo o de subir `max_instance_count`.
