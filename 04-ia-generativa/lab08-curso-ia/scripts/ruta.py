"""Fuente única de la RUTA de aprendizaje del lab 8 (ejercicios #1 a #26).

Genera EMPIEZA_AQUI.md y pone en cada README.md / INSTRUCCIONES.md un encabezado
"Ruta: ejercicio #N de 26" con enlaces al anterior y al siguiente. Si agregas o
reordenas un ejercicio, edita RUTA y vuelve a correr (no edites los encabezados a mano).

Correr (desde 04-ia-generativa/lab08-curso-ia/):   python scripts/ruta.py
"""
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# (carpeta, título, comando para empezar, tiempo)
P0, P1, P2 = "parte0_python", "parte1_fundamentos", "parte2_gcp"
RUTA = [
    (f"{P0}/01_primer_script", "Tu primer script", f"python {P0}/01_primer_script/ejercicio.py", "30 min"),
    (f"{P0}/02_listas_y_diccionarios", "Listas y diccionarios", f"python {P0}/02_listas_y_diccionarios/ejercicio.py", "40 min"),
    (f"{P0}/03_funciones", "Funciones", f"python {P0}/03_funciones/ejercicio.py", "40 min"),
    (f"{P0}/04_archivos_json_errores", "Archivos, JSON y errores", f"python {P0}/04_archivos_json_errores/ejercicio.py", "40 min"),
    (f"{P0}/05_clases_y_tipos", "Clases y tipos", f"python {P0}/05_clases_y_tipos/ejercicio.py", "40 min"),
    (f"{P1}/01_reglas_vs_aprendizaje", "Reglas vs. aprendizaje", f"python {P1}/01_reglas_vs_aprendizaje/spam.py", "10 min"),
    (f"{P1}/02_aprender_es_ajustar_numeros", "Aprender = ajustar números", f"python {P1}/02_aprender_es_ajustar_numeros/regresion.py", "15 min"),
    (f"{P1}/03_una_neurona", "Una neurona", f"python {P1}/03_una_neurona/perceptron.py", "10 min"),
    (f"{P1}/04_red_neuronal", "Red neuronal", f"python {P1}/04_red_neuronal/red_xor.py", "20 min"),
    (f"{P1}/05_tokens", "Tokens", f"python {P1}/05_tokens/tokens.py", "15 min"),
    (f"{P1}/06_embeddings", "Embeddings", f"python {P1}/06_embeddings/embeddings.py", "15 min"),
    (f"{P1}/07_siguiente_palabra", "Siguiente palabra", f"python {P1}/07_siguiente_palabra/bigramas.py", "15 min"),
    (f"{P1}/08_temperatura", "Temperatura", f"python {P1}/08_temperatura/temperatura.py", "10 min"),
    (f"{P1}/09_mini_rag", "Mini RAG", f"python {P1}/09_mini_rag/mini_rag.py", "25 min"),
    (f"{P2}/10_setup_gcp", "Preparar el entorno", "python 10_setup_gcp/verificar_entorno.py", "30 min"),
    (f"{P2}/11_gemini_sdk", "Gemini con el SDK", "python 11_gemini_sdk/hola_gemini.py", "20 min"),
    (f"{P2}/12_salida_estructurada", "Salida estructurada", "python 12_salida_estructurada/extraer_reglas.py", "30 min"),
    (f"{P2}/13_embeddings_rag", "RAG con embeddings", "python 13_embeddings_rag/rag_sas.py", "40 min"),
    (f"{P2}/14_agente_herramientas", "Agente con herramientas", "python 14_agente_herramientas/agente.py", "40 min"),
    (f"{P2}/15_multi_agente", "Multi-agente SAS → Python", "python 15_multi_agente/migrar.py", "60 min"),
    (f"{P2}/16_evaluacion", "Evaluación y quality gate", "python 16_evaluacion/evaluar.py", "40 min"),
    (f"{P2}/17_bigquery", "BigQuery", "python 17_bigquery/sas_a_bigquery.py", "40 min"),
    (f"{P2}/18_cloud_functions_storage", "Cloud Functions + Storage", "python 18_cloud_functions_storage/probar_local.py", "30 min"),
    (f"{P2}/19_cloud_run_api", "API en Cloud Run", "uvicorn --app-dir 19_cloud_run_api app:app --port 8080", "40 min"),
    (f"{P2}/20_composer_dataflow", "Dataflow y Composer", "python 20_composer_dataflow/pipeline_ventas_beam.py", "40 min"),
    (f"{P2}/21_monitoreo_gobernanza", "Monitoreo y gobernanza", "python 21_monitoreo_gobernanza/reporte_costos.py", "30 min"),
]
TOTAL = len(RUTA)
INICIO, FIN = "<!-- ruta:inicio -->", "<!-- ruta:fin -->"


def _entrada(carpeta: str) -> Path:
    """El archivo que conviene abrir primero en cada carpeta."""
    readme = RAIZ / carpeta / "README.md"
    return readme if readme.exists() else RAIZ / carpeta / "INSTRUCCIONES.md"


def _enlace(desde: Path, hacia: Path) -> str:
    return os.path.relpath(hacia, desde.parent).replace("\\", "/")


def _encabezado(archivo: Path, n: int) -> str:
    partes = [f"**Ruta de aprendizaje: ejercicio #{n} de {TOTAL}**"]
    if n > 1:
        carpeta, titulo = RUTA[n - 2][:2]
        partes.append(f"[← #{n - 1} {titulo}]({_enlace(archivo, _entrada(carpeta))})")
    if n < TOTAL:
        carpeta, titulo = RUTA[n][:2]
        partes.append(f"[#{n + 1} {titulo} →]({_enlace(archivo, _entrada(carpeta))})")
    partes.append(f"[ruta completa]({_enlace(archivo, RAIZ / 'EMPIEZA_AQUI.md')})")
    return f"{INICIO}\n> {' · '.join(partes)}\n{FIN}"


def poner_encabezados():
    for n, (carpeta, *_resto) in enumerate(RUTA, start=1):
        for nombre in ("README.md", "INSTRUCCIONES.md"):
            archivo = RAIZ / carpeta / nombre
            if not archivo.exists():
                continue
            texto = archivo.read_text(encoding="utf-8")
            texto = re.sub(rf"\n?{INICIO}.*?{FIN}\n?", "\n", texto, flags=re.S)   # quitar el anterior
            titulo, _, cuerpo = texto.partition("\n")
            archivo.write_text(f"{titulo}\n\n{_encabezado(archivo, n)}\n\n{cuerpo.lstrip()}", encoding="utf-8")


def generar_empieza_aqui():
    filas = []
    bloques = {P0: "Parte 0 — Python para IA", P1: "Parte 1 — Fundamentos de IA", P2: "Parte 2 — IA en Google Cloud"}
    parte_actual = None
    for n, (carpeta, titulo, comando, tiempo) in enumerate(RUTA, start=1):
        parte = carpeta.split("/")[0]
        if parte != parte_actual:
            parte_actual = parte
            extra = " (los comandos se corren desde `parte2_gcp/`)" if parte == P2 else ""
            filas.append(f"\n### {bloques[parte]}{extra}\n")
            filas.append("| ✔ | # | Ejercicio | Abre primero | Corre | Tiempo |")
            filas.append("|---|---|---|---|---|---|")
        entrada = _entrada(carpeta)
        filas.append(f"| ☐ | **#{n}** | {titulo} | [{entrada.relative_to(RAIZ).as_posix()}]"
                     f"({entrada.relative_to(RAIZ).as_posix()}) | `{comando}` | {tiempo} |")

    texto = f"""# EMPIEZA AQUÍ — la ruta del lab 8, en orden (#1 → #{TOTAL})

> Archivo generado por `scripts/ruta.py`. Para cambiar el orden, edita ese script y vuelve a correrlo.

Haz los ejercicios **en orden**: cada uno usa lo del anterior. En cada carpeta abre primero el
archivo de la columna "Abre primero", sigue sus pasos **#1, #2, #3...** y al terminar pasa al
siguiente número. Todos los comandos se escriben en una terminal abierta en `04-ia-generativa/lab08-curso-ia/`,
salvo los de la parte 2.

**¿Por dónde empiezo?**
- Nunca he programado en Python → empieza en **#1**.
- Sé Python pero no IA → empieza en **#6**.
- Sé los fundamentos de IA y quiero Google Cloud → empieza en **#15**.

**Antes del #1:** instala Python 3.12 y VS Code (ver [parte0_python/README.md](parte0_python/README.md)).
**Antes del #15:** crea el entorno de la parte 2 (ver el paso #1 de
[parte2_gcp/10_setup_gcp/INSTRUCCIONES.md](parte2_gcp/10_setup_gcp/INSTRUCCIONES.md)). Todo funciona gratis en modo simulado;
conectar a Google Cloud es opcional ([docs/CONECTAR_GCP.md](docs/CONECTAR_GCP.md)).
{chr(10).join(filas)}

## Cuando termines

- Preparación de entrevista: [docs/GUIA_ENTREVISTA.md](docs/GUIA_ENTREVISTA.md)
- Probar todo en GCP real: [docs/COMO_PROBAR_TODO.md](docs/COMO_PROBAR_TODO.md)
- Costos: [docs/COSTOS_GCP.pdf](docs/COSTOS_GCP.pdf)
"""
    (RAIZ / "EMPIEZA_AQUI.md").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    poner_encabezados()
    generar_empieza_aqui()
    print(f"Ruta de {TOTAL} ejercicios aplicada y EMPIEZA_AQUI.md generado.")
