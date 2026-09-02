# 0002 — Node.js + TypeScript, no Python, para el servidor MCP

**Status:** Accepted

## Context

lab1 y lab2 de este repo están en Python (FastAPI y Django). El SDK
oficial de Anthropic para MCP existe tanto en Python (`mcp`) como en
Node.js/TypeScript (`@modelcontextprotocol/sdk`), así que lab3 podía
mantenerse en Python por consistencia con el resto del repo, o cambiar de
stack si había una razón real para hacerlo.

## Decision

Construir lab3 en **Node.js + TypeScript**, rompiendo la consistencia de
lenguaje con lab1/lab2.

## Alternatives considered

- **Python, usando el SDK oficial `mcp`**: mantenía consistencia con
  lab1/lab2 (mismo lenguaje, mismo tipo de `venv` por laboratorio que ya
  documenta el README raíz) y habría sido perfectamente viable — el SDK de
  Python es funcionalmente equivalente para un servidor de este tamaño.
  Se descartó porque el ecosistema de MCP (documentación, ejemplos,
  servidores de referencia como Playwright MCP, el propio Claude Desktop)
  vive predominantemente en TypeScript/Node — aprender el patrón ahí deja
  al lab más cerca de lo que se va a encontrar al leer ejemplos reales
  fuera de este repo.
- **Automatización de navegador con Selenium (Python) en vez de
  Puppeteer (Node)**: Selenium es la opción Python más establecida para
  controlar un navegador, pero requiere un *driver* de navegador aparte
  (chromedriver) gestionado por separado del gestor de paquetes; Puppeteer
  descarga su propio Chromium como parte de `npm install` — una sola
  herramienta, un solo paso de instalación, que es justo lo que hace
  concreto el requisito de "instalar Chromium" de este lab (ver ADR 0004).

## Consequences

- lab3 necesita `node`/`npm` instalados en la máquina, no solo el
  `python -m venv` que ya usan lab1/lab2 — un requisito de entorno nuevo
  para quien solo haya corrido los otros labs de este repo.
- El README raíz documenta explícitamente esta diferencia de stack (ver
  tabla de laboratorios) en vez de esconderla, para que quede claro que no
  fue un descuido sino una decisión.
- Cualquier reuso de lógica entre labs (poco probable dado que no
  comparten dominio) tendría que pasar por HTTP/CLI, no por un import
  directo de Python — no era un factor real en esta decisión, pero es una
  consecuencia del cambio de lenguaje.
