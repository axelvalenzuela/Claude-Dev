"""Único punto de contacto con Vertex AI (Gemini + embeddings).

Tres cosas que puedes pedirle al modelo:

    generar(prompt, ...)        -> Respuesta   (texto o JSON con esquema)
    embeber(textos, tipo=...)   -> list[list[float]]
    SesionAgente(sistema, herramientas).enviar(...)  -> Paso (texto o llamadas a herramientas)

Con MODO=simulado las mismas funciones responden desde comun/simulado.py:
el resto del código NO sabe si está hablando con la nube o con el simulador.
Ese desacoplamiento es lo que permite probar todo sin credenciales (y lo que
un entrevistador quiere oír cuando pregunta "¿cómo pruebas código con LLMs?").
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel

from comun import simulado
from comun.config import config
from comun.observabilidad import log, registrar_llamada
from comun.precios import costo_usd


@dataclass
class Respuesta:
    texto: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    latencia_s: float
    costo_usd: float

    def como(self, esquema: type[BaseModel]) -> BaseModel:
        """Valida el JSON de la respuesta contra un modelo Pydantic."""
        return esquema.model_validate_json(self.texto)


# ---------------------------------------------------------------------------
# Conexión real (solo se usa con MODO=real)
# ---------------------------------------------------------------------------
_clientes: dict[str, Any] = {}


def _cliente(location: str):
    """Un cliente por región. Se crea la primera vez que se necesita."""
    if location not in _clientes:
        config.exigir_proyecto()
        # Import aquí adentro: en modo simulado ni siquiera hace falta el SDK.
        from google import genai

        # vertexai=True -> factura a TU proyecto de GCP y usa tus credenciales
        # ADC (gcloud auth application-default login). Sin esto el SDK
        # intentaría usar la Gemini Developer API con una API key.
        _clientes[location] = genai.Client(vertexai=True, project=config.proyecto, location=location)
    return _clientes[location]


def _con_reintentos(funcion: Callable[[], Any], intentos: int = 4):
    """Reintenta errores temporales con espera exponencial (2s, 4s, 8s).

    429 = te pasaste de la cuota (RESOURCE_EXHAUSTED), 500/503 = el servicio
    tuvo un problema momentáneo. Un 400 (prompt mal formado) o 403 (sin
    permiso) NO se reintenta: repetirlo daría el mismo error.
    """
    from google.genai import errors

    espera = 2
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except errors.APIError as e:
            if e.code in (429, 500, 503) and intento < intentos:
                log("WARNING", "reintentando llamada", codigo=e.code, intento=intento, espera_s=espera)
                time.sleep(espera)
                espera *= 2
                continue
            raise


# ---------------------------------------------------------------------------
# 1. Generar texto
# ---------------------------------------------------------------------------
def generar(
    prompt: str,
    *,
    rol: str = "general",
    sistema: str | None = None,
    temperatura: float | None = None,
    esquema: type[BaseModel] | None = None,
    modelo: str | None = None,
) -> Respuesta:
    """Manda un prompt y devuelve la respuesta con tokens, costo y latencia.

    rol:          etiqueta para logs/costos ("analista", "convertidor"...). En
                  modo simulado además decide qué respuesta falsa se devuelve.
    sistema:      instrucciones de sistema (quién es el modelo, reglas fijas).
    temperatura:  None = la del modelo. La guía de Gemini 3 recomienda dejar
                  el valor por defecto (1.0); en modelos 2.x se usaba ~0.2.
    esquema:      clase Pydantic -> el modelo responde JSON con esa forma.
    """
    modelo = modelo or config.modelo
    inicio = time.perf_counter()

    if config.es_real:
        from google.genai import types

        ajustes = types.GenerateContentConfig(
            system_instruction=sistema,
            temperature=temperatura,
            response_mime_type="application/json" if esquema else None,
            response_schema=esquema,
        )
        r = _con_reintentos(
            lambda: _cliente(config.region_modelos).models.generate_content(
                model=modelo, contents=prompt, config=ajustes
            )
        )
        texto = r.text or ""
        uso = r.usage_metadata
        tokens_entrada = uso.prompt_token_count or 0
        # Los "thinking tokens" (razonamiento interno) se cobran como salida.
        tokens_salida = (uso.candidates_token_count or 0) + (uso.thoughts_token_count or 0)
    else:
        texto = simulado.generar(rol, prompt)
        tokens_entrada = simulado.contar_tokens((sistema or "") + prompt)
        tokens_salida = simulado.contar_tokens(texto)

    respuesta = Respuesta(
        texto=texto,
        modelo=modelo,
        tokens_entrada=tokens_entrada,
        tokens_salida=tokens_salida,
        latencia_s=round(time.perf_counter() - inicio, 3),
        costo_usd=costo_usd(modelo, tokens_entrada, tokens_salida),
    )
    registrar_llamada(
        tipo="generar", rol=rol, modo=config.modo, modelo=modelo,
        tokens_entrada=tokens_entrada, tokens_salida=tokens_salida,
        costo_usd=respuesta.costo_usd, latencia_s=respuesta.latencia_s,
    )
    return respuesta


# ---------------------------------------------------------------------------
# 2. Embeddings
# ---------------------------------------------------------------------------
def embeber(textos: list[str], *, tipo: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Convierte textos en vectores.

    tipo: RETRIEVAL_DOCUMENT para lo que guardas en el índice,
          RETRIEVAL_QUERY para la pregunta del usuario. Usar el equivocado no
          da error: solo empeora la búsqueda en silencio (igual que en lab7).
    """
    if not textos:
        return []
    inicio = time.perf_counter()

    if config.es_real:
        from google.genai import types

        cliente = _cliente(config.region_embeddings)
        ajustes = types.EmbedContentConfig(task_type=tipo)
        # gemini-embedding-001 en Vertex acepta UN texto por petición;
        # text-embedding-005 acepta lotes. Por simplicidad vamos de uno en uno.
        vectores = []
        for t in textos:
            r = _con_reintentos(
                lambda t=t: cliente.models.embed_content(
                    model=config.modelo_embeddings, contents=t, config=ajustes
                )
            )
            vectores.append(list(r.embeddings[0].values))
    else:
        vectores = [simulado.embeber(t) for t in textos]

    tokens = sum(simulado.contar_tokens(t) for t in textos)   # aproximado en ambos modos
    registrar_llamada(
        tipo="embeber", rol=tipo, modo=config.modo, modelo=config.modelo_embeddings,
        tokens_entrada=tokens, tokens_salida=0,
        costo_usd=costo_usd(config.modelo_embeddings, tokens, 0),
        latencia_s=round(time.perf_counter() - inicio, 3),
    )
    return vectores


# ---------------------------------------------------------------------------
# 3. Agente con herramientas (function calling)
# ---------------------------------------------------------------------------
@dataclass
class LlamadaHerramienta:
    nombre: str
    argumentos: dict


@dataclass
class Paso:
    """Lo que decidió el modelo en un turno: responder, o pedir herramientas."""
    texto: str | None = None
    llamadas: list[LlamadaHerramienta] = field(default_factory=list)


class SesionAgente:
    """Conversación con memoria en la que el modelo puede pedir herramientas.

    Las herramientas son funciones normales de Python. El SDK lee su nombre,
    su docstring y sus type hints para describírselas al modelo: por eso el
    docstring de cada herramienta ES parte del prompt (ver micro lab 14).
    """

    def __init__(self, sistema: str, herramientas: list[Callable]):
        self.sistema = sistema
        self.herramientas = {f.__name__: f for f in herramientas}
        self._historial: list = []

    def enviar(self, mensaje: str) -> Paso:
        if config.es_real:
            from google.genai import types

            self._historial.append(types.Content(role="user", parts=[types.Part.from_text(text=mensaje)]))
        else:
            self._historial.append({"rol": "usuario", "texto": mensaje})
        return self._turno()

    def enviar_resultados(self, resultados: list[tuple[str, Any]]) -> Paso:
        if config.es_real:
            from google.genai import types

            partes = [types.Part.from_function_response(name=n, response={"resultado": r}) for n, r in resultados]
            self._historial.append(types.Content(role="user", parts=partes))
        else:
            for n, r in resultados:
                self._historial.append({"rol": "herramienta", "nombre": n, "resultado": r})
        return self._turno()

    def _turno(self) -> Paso:
        inicio = time.perf_counter()
        if config.es_real:
            from google.genai import types

            ajustes = types.GenerateContentConfig(
                system_instruction=self.sistema,
                tools=list(self.herramientas.values()),
                # Apagamos el "automatic function calling" del SDK para ver y
                # controlar nosotros cada paso del ciclo del agente.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            r = _con_reintentos(
                lambda: _cliente(config.region_modelos).models.generate_content(
                    model=config.modelo, contents=self._historial, config=ajustes
                )
            )
            # Guardamos el turno del modelo TAL CUAL (incluye las "thought
            # signatures" que Gemini 3 necesita de vuelta en el siguiente turno).
            self._historial.append(r.candidates[0].content)
            llamadas = [LlamadaHerramienta(fc.name, dict(fc.args or {})) for fc in (r.function_calls or [])]
            paso = Paso(texto=None if llamadas else (r.text or ""), llamadas=llamadas)
            uso = r.usage_metadata
            t_in = uso.prompt_token_count or 0
            t_out = (uso.candidates_token_count or 0) + (uso.thoughts_token_count or 0)
        else:
            texto, llamadas = simulado.turno_agente(self._historial)
            paso = Paso(texto=texto, llamadas=[LlamadaHerramienta(n, a) for n, a in llamadas])
            self._historial.append({"rol": "modelo", "texto": texto, "llamadas": llamadas})
            t_in = simulado.contar_tokens(str(self._historial))
            t_out = simulado.contar_tokens(str(texto or llamadas))

        registrar_llamada(
            tipo="agente", rol="agente", modo=config.modo, modelo=config.modelo,
            tokens_entrada=t_in, tokens_salida=t_out, costo_usd=costo_usd(config.modelo, t_in, t_out),
            latencia_s=round(time.perf_counter() - inicio, 3),
        )
        return paso
