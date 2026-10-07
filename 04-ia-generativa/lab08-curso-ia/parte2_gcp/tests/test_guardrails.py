from comun.guardrails import extraer_bloque_codigo, redactar_datos_sensibles, revisar_codigo_generado


def test_redacta_correo_y_tarjeta():
    texto, conteo = redactar_datos_sensibles("contacto: ana@acme.com, tarjeta 4111 1111 1111 1111")
    assert "ana@acme.com" not in texto
    assert "4111" not in texto
    assert conteo == {"CORREO": 1, "TARJETA": 1}


def test_texto_sin_datos_sensibles_no_cambia():
    texto, conteo = redactar_datos_sensibles("DATA x; SET y; RUN;")
    assert texto == "DATA x; SET y; RUN;"
    assert conteo == {}


def test_codigo_con_pandas_pasa():
    assert revisar_codigo_generado("import pandas as pd\n\ndef transformar(df):\n    return df\n") == []


def test_bloquea_imports_peligrosos():
    problemas = revisar_codigo_generado("import subprocess\nfrom os import system\n")
    assert any("subprocess" in p for p in problemas)
    assert any("os" in p for p in problemas)


def test_bloquea_eval_y_open():
    problemas = revisar_codigo_generado("eval('1')\nopen('x')\n")
    assert len(problemas) == 2


def test_reporta_sintaxis_invalida():
    assert "no es Python válido" in revisar_codigo_generado("def (:")[0]


def test_extrae_bloque_de_markdown():
    assert extraer_bloque_codigo("Aquí está:\n```python\nx = 1\n```\nListo") == "x = 1"
    assert extraer_bloque_codigo("SELECT 1", "sql") == "SELECT 1"
