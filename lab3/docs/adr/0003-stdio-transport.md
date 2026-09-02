# 0003 — Transporte stdio, no HTTP/SSE

**Status:** Accepted

## Context

MCP define más de un transporte para el canal cliente↔servidor: **stdio**
(el servidor es un subproceso local que habla JSON-RPC por su stdin/
stdout) y **HTTP con Server-Sent Events** (el servidor corre como un
proceso de red independiente, alcanzable por URL). Claude Desktop y Claude
Code soportan ambos. Había que elegir uno para lab3.

## Decision

Usar **`StdioServerTransport`** — el cliente MCP lanza `node dist/server.js`
como proceso hijo y le habla por stdin/stdout, sin abrir ningún puerto de
red.

## Alternatives considered

- **HTTP + SSE**: necesario si el servidor va a correr en una máquina
  distinta del cliente, ser compartido por varios clientes a la vez, o
  desplegarse como un servicio de larga duración (p. ej. detrás de un
  contenedor, como lab2 se despliega vía `lab2/infra/`). Para un lab local
  de un solo usuario y un solo cliente MCP corriendo en la misma máquina,
  eso es infraestructura de red que el lab no necesita — habría añadido un
  puerto que exponer/asegurar, un ciclo de vida de servidor independiente
  del cliente (arrancarlo, mantenerlo vivo, reiniciarlo), y una superficie
  de configuración mayor sin ningún beneficio real a este alcance.

## Consequences

- lab3 solo puede usarse con un cliente MCP que lo lance como subproceso
  local (Claude Desktop, Claude Code) — no es alcanzable por red, ni
  compartible entre varias máquinas o usuarios a la vez.
- No hay puerto que abrir, asegurar, ni documentar — el único requisito de
  red es el que ya tiene Chromium para llegar a los sitios que se le pida
  abrir.
- Migrar a HTTP/SSE en el futuro (si el lab creciera a necesitar acceso
  remoto) sería un cambio de transporte en `server.ts`
  (`StdioServerTransport` → el transporte HTTP del SDK), sin tocar
  `browser.ts` ni la definición de las herramientas — el SDK separa
  explícitamente "cómo llegan los mensajes" de "qué hace cada herramienta".
