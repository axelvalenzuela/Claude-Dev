"""Configuración compartida de pytest.

Los tests SIEMPRE corren en modo simulado: sin credenciales, sin red, sin costo.
Por eso pueden correr en GitHub Actions en cada push (ver .github/workflows/lab8-ci.yml).
Esto debe ir antes de importar comun/, porque config.py lee MODO al importarse.
"""
import os
import sys
from pathlib import Path

os.environ["MODO"] = "simulado"
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
