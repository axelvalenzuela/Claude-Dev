# Architecture Decision Records

Cada archivo aquí documenta una decisión de arquitectura de lab3: el
contexto que forzó a decidir, la decisión en sí, las alternativas que se
consideraron y se descartaron, y las consecuencias — incluidas las que no
son puramente positivas. Mismo formato que `lab2/docs/adr/`, para que
cualquiera que ya conozca ese repo reconozca la estructura de inmediato.

| # | Título | Status |
|---|---|---|
| [0001](0001-custom-mcp-server-not-prebuilt.md) | Un servidor MCP propio, no instalar uno ya publicado | Accepted |
| [0002](0002-nodejs-typescript-over-python.md) | Node.js + TypeScript, no Python, para el servidor MCP | Accepted |
| [0003](0003-stdio-transport.md) | Transporte stdio, no HTTP/SSE | Accepted |
| [0004](0004-bundled-chromium.md) | Chromium empaquetado (`puppeteer`), no un navegador del sistema | Accepted |
| [0005](0005-shared-browser-instance.md) | Un solo browser/page compartidos, no uno nuevo por llamada | Accepted |

## Formato

- **Status**: `Proposed`, `Accepted`, `Superseded by NNNN`, o `Deprecated`.
- **Context**: el problema/restricción que forzó la decisión — escrito
  para que alguien que no estuvo ahí entienda *por qué era una pregunta*.
- **Decision**: qué se eligió realmente, en una o dos frases.
- **Alternatives considered**: qué más estaba sobre la mesa, y por qué
  perdió — la parte que una decisión tomada en aislado (sin este registro)
  siempre pierde primero.
- **Consequences**: qué cuesta esta decisión, no solo qué gana — toda
  decisión real tiene ambos lados.
