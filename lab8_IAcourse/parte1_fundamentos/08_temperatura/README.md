# 08 — Temperatura

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #13 de 26** · [← #12 Siguiente palabra](../07_siguiente_palabra/README.md) · [#14 Mini RAG →](../09_mini_rag/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Idea:** el modelo da un puntaje (**logit**) a cada candidato; **softmax**
los convierte en probabilidades. La **temperatura** controla qué tan
"parejas" quedan antes de escoger:

| Temperatura | Efecto | Úsala para |
|---|---|---|
| ~0 – 0.3 | Casi siempre el favorito. Predecible. | Respuestas sobre hechos, código, RAG |
| ~1.0 | Las probabilidades "naturales" | Uso general |
| > 1.0 | Todo se empareja. Variado, a veces absurdo. | Lluvia de ideas |

```bash
python temperatura.py
```

## Qué observar

- Con 0.2, `azul` tiene 97.5 % y sale las 20 veces.
- Con 2.0 aparece hasta `delicioso` (*"el cielo hoy está delicioso"*).
- lab7 usa `temperature=0.2` en [src/gemini_client.py](../../../lab7/src/gemini_client.py):
  al responder sobre documentos se quiere precisión, no creatividad.

## Retos

1. Prueba temperatura `0.05` y `5.0`.
2. Cambia los `LOGITS` para que `nublado` sea el favorito.

**Siguiente:** juntamos todo → [09](../09_mini_rag/)
