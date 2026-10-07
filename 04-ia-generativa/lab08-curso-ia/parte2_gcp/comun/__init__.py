"""Código compartido por todos los micro labs de la parte 2.

Cada lab importa de aquí en vez de repetir la conexión a Vertex AI. Es el
mismo patrón que 04-ia-generativa/lab07-rag-vertex-cloudrun/src/gemini_client.py: UN solo lugar habla con la nube,
el resto del código trabaja con objetos de Python normales.

    config.py         lee el .env (modo simulado/real, proyecto, modelos)
    llm.py            generar texto, embeddings y sesiones de agente
    simulado.py       respuestas falsas para aprender sin gastar dinero
    esquemas.py       modelos Pydantic (la "forma" de las respuestas JSON)
    precios.py        tabla de precios -> costo en USD de cada llamada
    observabilidad.py logs JSON + registro de tokens/costo por llamada
    guardrails.py     reglas de seguridad antes/después de llamar al modelo
    validacion.py     ejecuta código generado y lo compara con el esperado
"""
