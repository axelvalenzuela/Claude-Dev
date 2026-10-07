# 0001 — Un servidor MCP propio, no instalar uno ya publicado

**Status:** Accepted

## Context

El objetivo de lab3 era un laboratorio *básico* de Claude MCP (Model
Context Protocol) usando Chromium. Existen servidores MCP de
automatización de navegador ya publicados (p. ej. Playwright MCP de
Microsoft) que se instalan y configuran sin escribir código propio.
También existía la opción de escribir un servidor MCP desde cero,
exponiendo herramientas propias sobre Puppeteer. Un lab tiene que decidir
cuál de los dos enseña mejor cómo funciona MCP realmente.

## Decision

Escribir un servidor MCP propio (`src/server.ts` + `src/tools/browser.ts`)
usando el SDK oficial `@modelcontextprotocol/sdk`, en vez de instalar un
servidor de automatización de navegador ya armado.

## Alternatives considered

- **Instalar un servidor MCP de navegador ya publicado (p. ej. Playwright
  MCP)**: habría sido más rápido de poner en marcha y probablemente más
  robusto (soporta más navegadores, más acciones), pero convierte el lab
  en "instalar y configurar una caja negra" — no deja ver cómo se declara
  una herramienta MCP (nombre, descripción, *schema* de entrada, handler),
  cómo se conecta el transporte, ni cómo un mensaje `tools/call` llega del
  modelo al código. Para un lab *básico* cuyo propósito es entender MCP,
  eso es justo la parte que no se quería ocultar.
- **No usar Chromium/navegador en absoluto, exponer herramientas
  triviales (echo, suma, etc.)**: habría sido aún más simple, pero no
  cumplía el requisito explícito del lab (Chromium) ni resultaba en algo
  con un caso de uso reconocible — abrir una página y leer su contenido es
  algo que cualquiera puede verificar visualmente que funcionó.

## Consequences

- El servidor tiene menos funcionalidad que un servidor de referencia
  publicado (3 herramientas, un solo navegador, sin manejo avanzado de
  errores, sin selectors/clicks/formularios) — es intencional: es un punto
  de partida para extender, no un reemplazo de un servidor de producción.
- Cualquier extensión futura del lab (más herramientas, más navegadores,
  manejo de pestañas múltiples) se hace directamente en `browser.ts`/
  `server.ts`, con el patrón ya establecido por las tres herramientas
  existentes como plantilla.
- Se depende directamente del SDK oficial de Anthropic
  (`@modelcontextprotocol/sdk`) en vez de la superficie ya empaquetada de
  un servidor de terceros — mayor control, pero también toda la
  responsabilidad de mantenerlo al día con el protocolo.
