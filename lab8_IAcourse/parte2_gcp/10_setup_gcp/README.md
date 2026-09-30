# 10 — Preparar el entorno de GCP

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #15 de 26** · [← #14 Mini RAG](../../parte1_fundamentos/09_mini_rag/README.md) · [#16 Gemini con el SDK →](../11_gemini_sdk/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** qué piezas necesita tu código para hablar con Vertex AI y cómo
diagnosticar cuando no puede.

## Conceptos

| Pieza | Qué es | Analogía |
|---|---|---|
| Proyecto | Contenedor de recursos y de facturación | Una "cuenta" separada para este lab |
| Facturación | Tarjeta/cuenta ligada al proyecto | Sin ella, Vertex AI responde 403 |
| API habilitada | Interruptor por servicio (`aiplatform.googleapis.com`) | Hay que "encender" cada servicio |
| IAM | Quién puede hacer qué (roles) | Llaves de cada puerta |
| ADC | *Application Default Credentials*: dónde busca credenciales el SDK | Tu gafete, sin copiar llaves a archivos |
| Región | Dónde corre el servicio (`us-central1`, `global`) | No todos los modelos están en todas |

El modo **simulado vs real** (`MODO` en `.env`) es el patrón que usan todos los labs:
el código de negocio no sabe si habla con la nube o con un simulador
([comun/llm.py](../comun/llm.py)). Así se prueba gratis y en CI.

## Archivos

- [verificar_entorno.py](verificar_entorno.py) — checklist automático con pistas de solución.
- [../.env.example](../.env.example) — todas las variables, comentadas.

## Para la entrevista

- *"¿Cómo se autentica tu app en GCP?"* → ADC: en local `gcloud auth application-default login`;
  en Cloud Run/Functions la cuenta de servicio del servicio. Nunca llaves JSON en el repo.
- *"¿Qué haces con un 403?"* → distinguir API deshabilitada vs rol faltante vs facturación (el mensaje lo dice).

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
