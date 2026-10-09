"""Genera docs/gcp-costs.pdf y docs/gcp-costs.md desde UNA sola fuente de datos.

Buena práctica de documentación: si los precios cambian, se editan AQUÍ y se
regeneran ambos archivos; así el PDF y el Markdown nunca se contradicen.

Correr (desde la raíz del repo):
    pip install reportlab==4.4.4
    python scripts/generar_costos.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DOCS = Path(__file__).resolve().parents[1] / "docs"
FECHA = "29 de septiembre de 2026"
TITULO = "el curso - Costos de GCP y qué te falta para conectarte"

RESUMEN = [
    "Practicar TODOS los labs de la parte 2 en modo real cuesta menos de 2 USD en total "
    "(casi todo cae en capas gratuitas). Si tu cuenta es nueva, Google da 300 USD de crédito por 90 días.",
    "Lo único caro de este curso es Cloud Composer (~400 USD/mes aunque no haga nada) y Vertex AI "
    "Vector Search (cobra por nodo encendido 24/7). Los labs NO los crean: se explican y se prueban local.",
    "Un presupuesto de GCP AVISA pero NO DETIENE el gasto. Para cortar el gasto: terraform destroy.",
    "Precios en USD, región us-central1, verificados el " + FECHA + ". Cambian seguido: confirma en "
    "cloud.google.com/pricing y en la calculadora (cloud.google.com/products/calculator).",
]

# Servicio | Para qué en los labs | Cómo cobra | Precio | Gratis cada mes | Costo de practicar | Riesgo y cómo evitarlo
SERVICIOS = [
    ["Vertex AI - Gemini", "Ejercicios 11 - 19: generar, analizar, convertir, documentar",
     "Por millón de tokens de entrada y de salida (salida incluye 'thinking')",
     "Flash-Lite 3.1: 0.25 / 1.50", "No (crédito de 300 USD si eres nuevo)", "< 1 USD",
     "Un agente en ciclo sin límite. Usa MAX_PASOS/MAX_INTENTOS y max-instances"],
    ["Vertex AI - Embeddings", "Ejercicios 13 y 17: vectores para RAG",
     "Por millón de tokens de entrada", "gemini-embedding-001: 0.15", "No", "< 0.01 USD",
     "Re-embeber todo en cada arranque. Guarda el índice (ejercicio 13 lo cachea)"],
    ["BigQuery - consultas", "Ejercicio 17: SQL migrado, dry run, VECTOR_SEARCH",
     "On-demand: por TiB leído (mínimo 10 MB por consulta)", "6.25 USD / TiB", "1 TiB",
     "0 USD", "SELECT * sobre tablas enormes. Usa dry run, particiones y columnas concretas"],
    ["BigQuery - almacenamiento", "Tablas ventas, auditoría, conocimiento",
     "Por GiB al mes (lógico)", "0.02 activo / 0.01 largo plazo", "10 GiB", "0 USD",
     "Datos que nadie borra. Particiona y pon expiración"],
    ["Cloud Storage", "Ejercicios 18 y 20: entrada/, resultados/, tmp/",
     "Por GB al mes + operaciones", "~0.020 USD / GB-mes (Standard)", "5 GB-mes (us-central1)",
     "0 USD", "Buckets olvidados. Terraform pone borrado automático a 30 días"],
    ["Cloud Run", "Ejercicio 19: API del migrador",
     "vCPU-segundo + GiB-segundo + peticiones (solo mientras atiende)",
     "0.000024 vCPU-s / 0.0000025 GiB-s / 0.40 por millón", "180,000 vCPU-s; 360,000 GiB-s; 2M peticiones",
     "0 USD", "min-instances > 0 cobra 24/7. Deja 0 y pon max-instances"],
    ["Cloud Functions (2a gen)", "Ejercicio 18: analiza cada .sas que se sube",
     "Igual que Cloud Run (corre sobre Cloud Run)", "Igual que Cloud Run", "Comparte la de Cloud Run",
     "0 USD", "Ciclo infinito si escribe en la carpeta que la dispara (el lab filtra entrada/)"],
    ["Cloud Build + Artifact Registry", "Construir imágenes al desplegar ejercicios 18 - 19",
     "Minutos de build / GB de imágenes guardadas", "Build ~0.006 USD/min; AR 0.10 USD/GB-mes",
     "2,500 min de build; 0.5 GB en AR", "< 0.10 USD", "Imágenes viejas acumuladas. Borra versiones antiguas"],
    ["Eventarc + Pub/Sub", "Disparador Storage -> Function (ejercicio 18)",
     "Por volumen de mensajes", "Centavos por millón de eventos", "10 GiB de Pub/Sub", "0 USD", "Mínimo"],
    ["Cloud Logging", "Ejercicio 21: logs JSON de cada llamada",
     "Por GiB ingerido", "0.50 USD / GiB", "50 GiB por proyecto", "0 USD",
     "Loguear prompts completos a gran escala. Loguea métricas, no textos enteros"],
    ["Dataflow", "Ejercicio 20 (opcional): el pipeline Beam en la nube",
     "vCPU-hora + GB-hora de los workers", "~0.056 USD vCPU-h (batch)", "No", "~0.05 USD por corrida",
     "Jobs de streaming que quedan corriendo. Cancela con gcloud dataflow jobs cancel"],
    ["Cloud Composer 3", "Ejercicio 20 (opcional): el DAG de Airflow",
     "DCU-hora del entorno, corra o no corra nada", "0.06 USD / DCU-hora", "No",
     "~13 USD por día que exista", "CARO: ~400 USD/mes. Si lo creas, destrúyelo el mismo día"],
    ["Vertex AI Vector Search", "No se usa (se explica como alternativa)",
     "Por nodo/hora del índice desplegado", "Desde ~70 USD/mes por nodo", "No", "0 USD (no se crea)",
     "Índice desplegado olvidado. Para aprender usa BigQuery VECTOR_SEARCH"],
    ["Presupuesto (Billing Budgets)", "infra/presupuesto.tf: alertas 50/90/100%",
     "Gratis", "0", "-", "0 USD", "Moneda distinta a la de tu cuenta de facturación = error al aplicar"],
]

# Modelo | Entrada | Salida | Para qué
MODELOS = [
    ["gemini-3.1-flash-lite", "0.25", "1.50", "Default de los labs. Barato: clasificar, extraer, documentar"],
    ["gemini-3-flash", "0.50", "3.00", "Balance calidad/precio"],
    ["gemini-3.8-flash", "0.75 (1.50 desde ene-2027)", "3.75 (7.50 desde ene-2027)",
     "El Flash más nuevo: buena opción para convertir código"],
    ["gemini-3.5-flash", "1.50", "9.00", "Flash de alta capacidad"],
    ["gemini-3.1-pro", "2.00 (4.00 >200K tokens)", "12.00 (18.00 >200K)", "Programas complejos, macros, razonamiento"],
    ["gemini-2.5-flash (05-rag-app-cloud-run)", "0.30", "2.50", "SE RETIRA ~16-20 oct 2026: migra 05-rag-app-cloud-run a un modelo 3.x"],
    ["Batch API", "-50 %", "-50 %", "Migraciones masivas que no necesitan respuesta inmediata"],
    ["Context caching", "hasta -90 % en entrada repetida", "-",
     "El mismo prompt de sistema + reglas en miles de llamadas"],
]

# Supuesto: 5,000 programas; por programa ~40K tokens de entrada y ~10K de salida sumando
# analista + convertidor (2 intentos promedio) + documentador + juez.
PROYECCION = [
    ["gemini-3.1-flash-lite", "0.025", "125", "63"],
    ["gemini-3.8-flash (precio intro)", "0.068", "338", "169"],
    ["gemini-3.1-pro", "0.200", "1,000", "500"],
]

# Requisito | Cómo se consigue | Comando / dónde | Lo verifica
CONECTAR = [
    ["Cuenta de Google Cloud con facturación", "Alta en console.cloud.google.com (pide tarjeta; 300 USD de crédito)",
     "gcloud billing accounts list", "-"],
    ["Proyecto dedicado al lab", "Crear proyecto y ligarle la facturación",
     "gcloud projects create ID ; gcloud billing projects link ID --billing-account=...", "ejercicio 10"],
    ["gcloud CLI", "Instalar Google Cloud SDK", "cloud.google.com/sdk/docs/install", "ejercicio 10"],
    ["Credenciales locales (ADC)", "Login de aplicación (sin llaves JSON)",
     "gcloud auth application-default login", "ejercicio 10"],
    ["APIs y recursos", "Terraform crea APIs, bucket, dataset, tablas, cuenta de servicio y permisos",
     "cd infra ; terraform init ; terraform apply", "ejercicios 17 - 19"],
    ["Rol para ti", "Owner/Editor del proyecto o, mínimo, Vertex AI User + BigQuery User",
     "IAM y administración > IAM", "ejercicio 10"],
    ["Configuración", "Copiar .env.example a .env y poner MODO=real y tu GCP_PROJECT_ID",
     "04-vertex-ai-projects/.env", "ejercicio 10"],
    ["Modelo disponible", "Confirmar que el ID de GEMINI_MODEL existe en tu región",
     "Vertex AI > Model Garden", "ejercicio 10"],
    ["Terraform (opcional pero recomendado)", "Instalar Terraform >= 1.6", "developer.hashicorp.com/terraform/install",
     "infra/"],
    ["Presupuesto con alertas", "billing_account_id en terraform.tfvars", "infra/presupuesto.tf", "-"],
]

FUENTES = [
    "Vertex AI / Gemini: cloud.google.com/vertex-ai/generative-ai/pricing y ai.google.dev/gemini-api/docs/pricing",
    "BigQuery: cloud.google.com/bigquery/pricing  |  Cloud Run y Functions: cloud.google.com/run/pricing",
    "Cloud Composer: cloud.google.com/composer/pricing  |  Retiro de Gemini 2.5: notas de versión de Vertex AI",
    "Estimaciones de terceros usadas para contrastar: cloudzero.com (Vertex AI pricing 2026), nops.io (Composer)",
]


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _estilos():
    base = getSampleStyleSheet()
    celda = ParagraphStyle("celda", parent=base["BodyText"], fontSize=7.4, leading=9, alignment=TA_LEFT)
    cabecera = ParagraphStyle("cab", parent=celda, textColor=colors.white, fontName="Helvetica-Bold")
    return base, celda, cabecera


def _tabla(filas, encabezados, anchos, celda, cabecera):
    datos = [[Paragraph(h, cabecera) for h in encabezados]]
    datos += [[Paragraph(str(c), celda) for c in fila] for fila in filas]
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f7")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9aa7b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawString(1.2 * cm, 0.8 * cm, f"{TITULO} - verificado el {FECHA} - generado por scripts/generar_costos.py")
    canvas.drawRightString(26.7 * cm, 0.8 * cm, f"Página {doc.page}")
    canvas.restoreState()


def generar_pdf(ruta: Path):
    base, celda, cabecera = _estilos()
    h1, h2, normal = base["Title"], base["Heading2"], base["BodyText"]
    historia = [Paragraph(TITULO, h1)]
    historia += [Paragraph("- " + r, normal) for r in RESUMEN]

    historia += [Spacer(1, 8), Paragraph("1. Matriz de costos por servicio", h2)]
    historia.append(_tabla(
        SERVICIOS,
        ["Servicio", "Para qué en los labs", "Cómo cobra", "Precio (USD)", "Gratis cada mes",
         "Costo de practicar", "Riesgo y cómo evitarlo"],
        [3.2, 4.2, 4.0, 3.6, 3.4, 2.3, 5.0], celda, cabecera))

    historia += [PageBreak(), Paragraph("2. Modelos Gemini en Vertex AI (USD por millón de tokens)", h2)]
    historia.append(_tabla(MODELOS, ["Modelo / opción", "Entrada", "Salida", "Cuándo usarlo"],
                           [5.5, 5.0, 5.0, 10.2], celda, cabecera))

    historia += [Spacer(1, 10), Paragraph("3. Proyección para el proyecto real: migrar 5,000 programas SAS", h2)]
    historia.append(Paragraph(
        "Supuesto: por programa ~40K tokens de entrada y ~10K de salida (analista + convertidor con 2 intentos "
        "promedio + documentador + juez). Solo tokens de IA; la infraestructura con uso moderado suma decenas "
        "de USD al mes. Mide con 10-20 programas reales (ejercicio 21) antes de presupuestar.", normal))
    historia.append(_tabla(
        PROYECCION, ["Modelo", "USD por programa", "USD total (5,000)", "USD total con Batch API (-50%)"],
        [7.0, 5.0, 5.5, 8.2], celda, cabecera))

    historia += [PageBreak(), Paragraph("4. Qué te falta para conectar los labs a GCP", h2)]
    historia.append(_tabla(CONECTAR, ["Requisito", "Cómo se consigue", "Comando / dónde", "Lo verifica"],
                           [5.0, 8.0, 10.0, 2.7], celda, cabecera))
    historia += [Spacer(1, 10), Paragraph("Fuentes", h2)]
    historia += [Paragraph("- " + f, normal) for f in FUENTES]

    doc = SimpleDocTemplate(str(ruta), pagesize=landscape(letter), leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.4 * cm, title=TITULO, author="ai-engineer-gcp-aws")
    doc.build(historia, onFirstPage=_pie, onLaterPages=_pie)


# ---------------------------------------------------------------------------
# Markdown (misma información, para leer en GitHub)
# ---------------------------------------------------------------------------
def _md_tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def generar_md(ruta: Path):
    partes = [
        f"# {TITULO}",
        "> Archivo generado por `scripts/generar_costos.py` (misma fuente que `gcp-costs.pdf`). "
        "No lo edites a mano: edita el script y regenera.",
        "\n".join(f"- {r}" for r in RESUMEN),
        "## 1. Matriz de costos por servicio",
        _md_tabla(["Servicio", "Para qué en los labs", "Cómo cobra", "Precio (USD)", "Gratis cada mes",
                   "Costo de practicar", "Riesgo y cómo evitarlo"], SERVICIOS),
        "## 2. Modelos Gemini en Vertex AI (USD por millón de tokens)",
        _md_tabla(["Modelo / opción", "Entrada", "Salida", "Cuándo usarlo"], MODELOS),
        "## 3. Proyección: migrar 5,000 programas SAS",
        "Supuesto: por programa ~40K tokens de entrada y ~10K de salida (todos los agentes, 2 intentos promedio).",
        _md_tabla(["Modelo", "USD por programa", "USD total (5,000)", "USD con Batch API (-50%)"], PROYECCION),
        "## 4. Qué te falta para conectar los labs a GCP",
        _md_tabla(["Requisito", "Cómo se consigue", "Comando / dónde", "Lo verifica"], CONECTAR),
        "## Fuentes",
        "\n".join(f"- {f}" for f in FUENTES),
    ]
    ruta.write_text("\n\n".join(partes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    generar_pdf(DOCS / "gcp-costs.pdf")
    generar_md(DOCS / "gcp-costs.md")
    print(f"Generados {DOCS / 'gcp-costs.pdf'} y {DOCS / 'gcp-costs.md'}")
