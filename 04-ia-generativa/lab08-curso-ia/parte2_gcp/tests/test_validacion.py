import pandas as pd

from comun.config import RAIZ
from comun.simulado import _VENTAS_CON_ERROR, _VENTAS_CORRECTO
from comun.validacion import comparar, ejecutar_y_comparar

DATOS = RAIZ / "comun" / "datos"
ENTRADA, ESPERADO = DATOS / "ventas.csv", DATOS / "esperado_resumen_ventas.csv"


def test_codigo_correcto_reconcilia():
    assert ejecutar_y_comparar(_VENTAS_CORRECTO, ENTRADA, ESPERADO).ok


def test_codigo_con_error_de_negocio_se_detecta():
    resultado = ejecutar_y_comparar(_VENTAS_CON_ERROR, ENTRADA, ESPERADO)
    assert not resultado.ok
    assert any("CENTRO" in p for p in resultado.problemas)


def test_codigo_que_truena_se_reporta():
    codigo = "import pandas as pd\n\ndef transformar(df):\n    return df['no_existe']\n"
    resultado = ejecutar_y_comparar(codigo, ENTRADA, ESPERADO)
    assert not resultado.ok
    assert "falló al ejecutarse" in resultado.problemas[0]


def test_codigo_peligroso_no_se_ejecuta():
    resultado = ejecutar_y_comparar("import os\n\ndef transformar(df):\n    return df\n", ENTRADA, ESPERADO)
    assert resultado.problemas == ["Importa un módulo no permitido: os"]


def test_comparar_ignora_orden_de_filas_y_tolera_redondeo():
    esperado = pd.DataFrame({"k": ["a", "b"], "v": [1.0, 2.0]})
    obtenido = pd.DataFrame({"k": ["b", "a"], "v": [2.004, 1.0]})
    assert comparar(obtenido, esperado).ok


def test_comparar_detecta_columnas_distintas():
    esperado = pd.DataFrame({"k": ["a"], "v": [1.0]})
    obtenido = pd.DataFrame({"k": ["a"], "valor": [1.0]})
    assert "Columnas distintas" in comparar(obtenido, esperado).problemas[0]
