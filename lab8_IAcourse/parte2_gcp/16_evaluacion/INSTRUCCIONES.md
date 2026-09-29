# 16 — Instrucciones

## Paso 1 — Tests automáticos

```bash
pytest -v            # desde parte2_gcp/: 20 tests, ~10 segundos, siempre en simulado
```

## Paso 2 — Evaluación con quality gate

```bash
python 16_evaluacion/evaluar.py
echo $?              # 0 = pasa, 1 = falla (CI usa este código de salida)
```

## Paso 3 — Romperlo a propósito (la mejor forma de entenderlo)

1. En [casos_golden.json](casos_golden.json) agrega `"PROC FREQ"` a `construcciones_esperadas` de `ventas.sas`.
2. Corre `evaluar.py`: baja el recall y el quality gate dice `FALLA`.
3. Regresa el archivo como estaba.

## Paso 4 — En real

Con `MODO=real`, `evaluar.py` mide al Gemini de verdad. Córrelo **antes y después** de cambiar
un prompt en `comun/agentes.py` y compara la tabla. Esa es la forma profesional de "mejorar un prompt".

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Un test falla tras cambiar `comun/` | Rompiste un contrato | Lee el `assert`; los tests dicen qué comportamiento se esperaba |
| Quality gate falla en real pero no en simulado | El modelo real rinde distinto | Revisa por caso qué métrica bajó; mejora el prompt del agente responsable |
| Resultados distintos en cada corrida real | No determinismo | Corre N veces y promedia; umbrales con margen |
| El juez da siempre 5 | Rúbrica débil | Rúbrica con criterios verificables y ejemplos de 2 y de 5 |
| CI rojo en GitHub | Algún paso falló | Pestaña Actions → job → paso en rojo → mismo comando en local |

## Retos

1. Agrega un caso nuevo al golden set con su programa SAS.
2. Agrega la métrica "precisión" (reglas inventadas que no estaban en lo esperado).
