# Lab 8 - Costos de GCP y qué te falta para conectarte

> Archivo generado por `scripts/generar_costos.py` (misma fuente que `COSTOS_GCP.pdf`). No lo edites a mano: edita el script y regenera.

- Practicar TODOS los labs de la parte 2 en modo real cuesta menos de 2 USD en total (casi todo cae en capas gratuitas). Si tu cuenta es nueva, Google da 300 USD de crédito por 90 días.
- Lo único caro de este curso es Cloud Composer (~400 USD/mes aunque no haga nada) y Vertex AI Vector Search (cobra por nodo encendido 24/7). Los labs NO los crean: se explican y se prueban local.
- Un presupuesto de GCP AVISA pero NO DETIENE el gasto. Para cortar el gasto: terraform destroy.
- Precios en USD, región us-central1, verificados el 29 de septiembre de 2026. Cambian seguido: confirma en cloud.google.com/pricing y en la calculadora (cloud.google.com/products/calculator).

## 1. Matriz de costos por servicio

| Servicio | Para qué en los labs | Cómo cobra | Precio (USD) | Gratis cada mes | Costo de practicar | Riesgo y cómo evitarlo |
|---|---|---|---|---|---|---|
| Vertex AI - Gemini | Labs 11-19: generar, analizar, convertir, documentar | Por millón de tokens de entrada y de salida (salida incluye 'thinking') | Flash-Lite 3.1: 0.25 / 1.50 | No (crédito de 300 USD si eres nuevo) | < 1 USD | Un agente en ciclo sin límite. Usa MAX_PASOS/MAX_INTENTOS y max-instances |
| Vertex AI - Embeddings | Labs 13 y 17: vectores para RAG | Por millón de tokens de entrada | gemini-embedding-001: 0.15 | No | < 0.01 USD | Re-embeber todo en cada arranque. Guarda el índice (lab 13 lo cachea) |
| BigQuery - consultas | Lab 17: SQL migrado, dry run, VECTOR_SEARCH | On-demand: por TiB leído (mínimo 10 MB por consulta) | 6.25 USD / TiB | 1 TiB | 0 USD | SELECT * sobre tablas enormes. Usa dry run, particiones y columnas concretas |
| BigQuery - almacenamiento | Tablas ventas, auditoría, conocimiento | Por GiB al mes (lógico) | 0.02 activo / 0.01 largo plazo | 10 GiB | 0 USD | Datos que nadie borra. Particiona y pon expiración |
| Cloud Storage | Labs 18 y 20: entrada/, resultados/, tmp/ | Por GB al mes + operaciones | ~0.020 USD / GB-mes (Standard) | 5 GB-mes (us-central1) | 0 USD | Buckets olvidados. Terraform pone borrado automático a 30 días |
| Cloud Run | Lab 19: API del migrador | vCPU-segundo + GiB-segundo + peticiones (solo mientras atiende) | 0.000024 vCPU-s / 0.0000025 GiB-s / 0.40 por millón | 180,000 vCPU-s; 360,000 GiB-s; 2M peticiones | 0 USD | min-instances > 0 cobra 24/7. Deja 0 y pon max-instances |
| Cloud Functions (2a gen) | Lab 18: analiza cada .sas que se sube | Igual que Cloud Run (corre sobre Cloud Run) | Igual que Cloud Run | Comparte la de Cloud Run | 0 USD | Ciclo infinito si escribe en la carpeta que la dispara (el lab filtra entrada/) |
| Cloud Build + Artifact Registry | Construir imágenes al desplegar labs 18-19 | Minutos de build / GB de imágenes guardadas | Build ~0.006 USD/min; AR 0.10 USD/GB-mes | 2,500 min de build; 0.5 GB en AR | < 0.10 USD | Imágenes viejas acumuladas. Borra versiones antiguas |
| Eventarc + Pub/Sub | Disparador Storage -> Function (lab 18) | Por volumen de mensajes | Centavos por millón de eventos | 10 GiB de Pub/Sub | 0 USD | Mínimo |
| Cloud Logging | Lab 21: logs JSON de cada llamada | Por GiB ingerido | 0.50 USD / GiB | 50 GiB por proyecto | 0 USD | Loguear prompts completos a gran escala. Loguea métricas, no textos enteros |
| Dataflow | Lab 20 (opcional): el pipeline Beam en la nube | vCPU-hora + GB-hora de los workers | ~0.056 USD vCPU-h (batch) | No | ~0.05 USD por corrida | Jobs de streaming que quedan corriendo. Cancela con gcloud dataflow jobs cancel |
| Cloud Composer 3 | Lab 20 (opcional): el DAG de Airflow | DCU-hora del entorno, corra o no corra nada | 0.06 USD / DCU-hora | No | ~13 USD por día que exista | CARO: ~400 USD/mes. Si lo creas, destrúyelo el mismo día |
| Vertex AI Vector Search | No se usa (se explica como alternativa) | Por nodo/hora del índice desplegado | Desde ~70 USD/mes por nodo | No | 0 USD (no se crea) | Índice desplegado olvidado. Para aprender usa BigQuery VECTOR_SEARCH |
| Presupuesto (Billing Budgets) | infra/presupuesto.tf: alertas 50/90/100% | Gratis | 0 | - | 0 USD | Moneda distinta a la de tu cuenta de facturación = error al aplicar |

## 2. Modelos Gemini en Vertex AI (USD por millón de tokens)

| Modelo / opción | Entrada | Salida | Cuándo usarlo |
|---|---|---|---|
| gemini-3.1-flash-lite | 0.25 | 1.50 | Default de los labs. Barato: clasificar, extraer, documentar |
| gemini-3-flash | 0.50 | 3.00 | Balance calidad/precio |
| gemini-3.8-flash | 0.75 (1.50 desde ene-2027) | 3.75 (7.50 desde ene-2027) | El Flash más nuevo: buena opción para convertir código |
| gemini-3.5-flash | 1.50 | 9.00 | Flash de alta capacidad |
| gemini-3.1-pro | 2.00 (4.00 >200K tokens) | 12.00 (18.00 >200K) | Programas complejos, macros, razonamiento |
| gemini-2.5-flash (lab7) | 0.30 | 2.50 | SE RETIRA ~16-20 oct 2026: migra lab7 a un modelo 3.x |
| Batch API | -50 % | -50 % | Migraciones masivas que no necesitan respuesta inmediata |
| Context caching | hasta -90 % en entrada repetida | - | El mismo prompt de sistema + reglas en miles de llamadas |

## 3. Proyección: migrar 5,000 programas SAS

Supuesto: por programa ~40K tokens de entrada y ~10K de salida (todos los agentes, 2 intentos promedio).

| Modelo | USD por programa | USD total (5,000) | USD con Batch API (-50%) |
|---|---|---|---|
| gemini-3.1-flash-lite | 0.025 | 125 | 63 |
| gemini-3.8-flash (precio intro) | 0.068 | 338 | 169 |
| gemini-3.1-pro | 0.200 | 1,000 | 500 |

## 4. Qué te falta para conectar los labs a GCP

| Requisito | Cómo se consigue | Comando / dónde | Lo verifica |
|---|---|---|---|
| Cuenta de Google Cloud con facturación | Alta en console.cloud.google.com (pide tarjeta; 300 USD de crédito) | gcloud billing accounts list | - |
| Proyecto dedicado al lab | Crear proyecto y ligarle la facturación | gcloud projects create ID ; gcloud billing projects link ID --billing-account=... | lab 10 |
| gcloud CLI | Instalar Google Cloud SDK | cloud.google.com/sdk/docs/install | lab 10 |
| Credenciales locales (ADC) | Login de aplicación (sin llaves JSON) | gcloud auth application-default login | lab 10 |
| APIs y recursos | Terraform crea APIs, bucket, dataset, tablas, cuenta de servicio y permisos | cd infra ; terraform init ; terraform apply | labs 17-19 |
| Rol para ti | Owner/Editor del proyecto o, mínimo, Vertex AI User + BigQuery User | IAM y administración > IAM | lab 10 |
| Configuración | Copiar .env.example a .env y poner MODO=real y tu GCP_PROJECT_ID | parte2_gcp/.env | lab 10 |
| Modelo disponible | Confirmar que el ID de GEMINI_MODEL existe en tu región | Vertex AI > Model Garden | lab 10 |
| Terraform (opcional pero recomendado) | Instalar Terraform >= 1.6 | developer.hashicorp.com/terraform/install | infra/ |
| Presupuesto con alertas | billing_account_id en terraform.tfvars | infra/presupuesto.tf | - |

## Fuentes

- Vertex AI / Gemini: cloud.google.com/vertex-ai/generative-ai/pricing y ai.google.dev/gemini-api/docs/pricing
- BigQuery: cloud.google.com/bigquery/pricing  |  Cloud Run y Functions: cloud.google.com/run/pricing
- Cloud Composer: cloud.google.com/composer/pricing  |  Retiro de Gemini 2.5: notas de versión de Vertex AI
- Estimaciones de terceros usadas para contrastar: cloudzero.com (Vertex AI pricing 2026), nops.io (Composer)
