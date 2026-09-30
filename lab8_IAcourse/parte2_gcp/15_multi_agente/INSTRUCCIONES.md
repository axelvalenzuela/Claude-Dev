# 15 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #20 de 26** · [← #19 Agente con herramientas](../14_agente_herramientas/README.md) · [#21 Evaluación y quality gate →](../16_evaluacion/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Correr en simulado

```bash
python 15_multi_agente/migrar.py                  # ventas.sas: falla 1 vez, se corrige, APROBADO
python 15_multi_agente/migrar.py clientes.sas     # sin datos de prueba: REQUIERE_REVISION
```

Resultados en `salida/<programa>/`: `transformar.py`, `DOCUMENTACION.md`, `analisis.json`, `bitacora.txt`.

## Paso #2 — Leer el código en este orden

1. [comun/orquestador.py](../comun/orquestador.py) → función `migrar`: los pasos 1, 2 y 3.
2. [comun/agentes.py](../comun/agentes.py) → las 3 instrucciones de sistema (`SISTEMA_*`) y cómo se arma la `RETROALIMENTACION`.
3. [comun/validacion.py](../comun/validacion.py) → `ejecutar_y_comparar` y `comparar`.
4. [comun/simulado.py](../comun/simulado.py) → `_VENTAS_CON_ERROR`: el error "sembrado" (umbral sobre `monto` en vez de `total_con_iva`).

## Qué observar

- Intento 1: el validador lista las filas exactas que no cuadran.
- Intento 2: el convertidor recibió esa lista y corrigió.
- El error sembrado es realista: **una venta de 8,700 no pasa 10,000, pero con IVA (10,092) sí**.
  Es el tipo de error que un revisor humano no ve y la reconciliación sí.

## Paso #3 — En real

`MODO=real` y corre otra vez. Gemini puede acertar al primer intento o no. Prueba también con un
modelo más barato/caro en `GEMINI_MODEL` y compara intentos y costo.

## Versión con ADK

Solo en real (ADK llama a Vertex directamente):

```bash
pip install google-adk==2.10.0
cd 15_multi_agente
cp adk_migracion/.env.example adk_migracion/.env      # pon tu proyecto
adk web            # abre http://localhost:8000, elige "adk_migracion" y pega el contenido de ventas.sas
# o en terminal:  adk run adk_migracion
```

En `adk web` verás el árbol de eventos: qué agente habló, qué herramienta llamó, cuántas vueltas dio el `LoopAgent`.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Siempre `REQUIERE_REVISION` en real | El convertidor no respeta el contrato | Lee `bitacora.txt`: ¿columnas distintas? ¿imports prohibidos? Refuerza `SISTEMA_CONVERTIDOR` |
| "Columnas distintas" | Nombres u orden de columnas | El contrato ya las pasa; revisa que el modelo no renombre |
| "Importa un módulo no permitido" | El modelo usó `os`, `re`, etc. | Guardrail funcionando; si el módulo es seguro, agrégalo a `MODULOS_PERMITIDOS` |
| "tardó más de 30s" | Ciclo infinito en el código generado | Timeout funcionando; cuenta como intento fallido |
| Diferencias de centavos | Redondeo / float | `tolerancia` en `comparar`; en producción usa `Decimal`/NUMERIC para dinero |
| `ValidationError` del analista | JSON fuera de esquema | Ver lab 12 |
| ADK: `No root_agent found` | Corriste `adk web` desde otra carpeta | Córrelo desde `15_multi_agente/` |
| ADK: error de credenciales | Falta `adk_migracion/.env` o ADC | Copia el `.env.example` y `gcloud auth application-default login` |

## Retos

1. Crea `comun/datos/inventario.csv` y su `esperado_...csv`, regístralos en `CASOS` (orquestador) y migra `inventario.sas`.
2. Usa un modelo distinto para el convertidor que para el documentador (parámetro `modelo=` de `generar`).
3. Agrega un 4.º agente "Revisor" que, antes del validador, revise legibilidad del código (y mide si mejora algo).
