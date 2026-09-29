"""Pruebas de punta a punta de los flujos, en modo simulado."""
import importlib.util
import sys

import pytest

from comun import llm
from comun.config import RAIZ
from comun.esquemas import AnalisisSAS
from comun.orquestador import migrar
from comun.precios import costo_usd


def _cargar(ruta_relativa: str, nombre: str):
    """Importa un archivo cuya carpeta empieza con número (no es un nombre de paquete válido)."""
    ruta = RAIZ / ruta_relativa
    sys.path.insert(0, str(ruta.parent))
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_costo_por_millon():
    assert costo_usd("gemini-3.1-flash-lite", 1_000_000, 1_000_000) == pytest.approx(1.75)
    assert costo_usd("modelo-desconocido", 100, 100) == 0.0


def test_salida_estructurada_valida_contra_esquema():
    sas = (RAIZ / "comun" / "sas" / "ventas.sas").read_text(encoding="utf-8")
    analisis = llm.generar(sas, rol="analista", esquema=AnalisisSAS).como(AnalisisSAS)
    assert {r.tipo for r in analisis.reglas} >= {"filtro", "calculo", "clasificacion", "agregacion"}


def test_migracion_ventas_se_autocorrige_y_aprueba():
    sas = (RAIZ / "comun" / "sas" / "ventas.sas").read_text(encoding="utf-8")
    resultado = migrar(sas, "ventas.sas", avisar=lambda _m: None)
    assert resultado.estado == "APROBADO"
    assert resultado.intentos == 2            # el simulador falla a propósito el primer intento
    assert resultado.costo_usd > 0


def test_migracion_sin_datos_de_prueba_requiere_revision():
    sas = (RAIZ / "comun" / "sas" / "clientes.sas").read_text(encoding="utf-8")
    assert migrar(sas, "clientes.sas", avisar=lambda _m: None).estado == "REQUIERE_REVISION"


def test_agente_usa_herramientas_y_responde():
    agente = _cargar("14_agente_herramientas/agente.py", "agente_lab14")
    respuesta = agente.ejecutar_agente("¿Cuál programa es el más complejo?")
    assert "clientes.sas" in respuesta


def test_api_cloud_run():
    from fastapi.testclient import TestClient

    app = _cargar("19_cloud_run_api/app.py", "app_lab19").app
    cliente = TestClient(app)
    assert cliente.get("/salud").json()["estado"] == "ok"

    sas = (RAIZ / "comun" / "sas" / "ventas.sas").read_text(encoding="utf-8")
    r = cliente.post("/migrar", json={"programa": "ventas.sas", "codigo_sas": sas})
    assert r.status_code == 200
    assert r.json()["estado"] == "APROBADO"
    assert cliente.post("/migrar", json={"codigo_sas": "x"}).status_code == 422   # muy corto


def test_cloud_function_ignora_archivos_fuera_de_entrada(tmp_path):
    from cloudevents.http import CloudEvent

    funcion = _cargar("18_cloud_functions_storage/funcion/main.py", "funcion_lab18")
    evento = CloudEvent({"type": "google.cloud.storage.object.v1.finalized", "source": "//prueba"},
                        {"bucket": "b", "name": "resultados/x.json"})
    assert funcion.analizar_sas(evento) is None      # no intenta leer nada: no truena
