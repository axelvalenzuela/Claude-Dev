# 02 · MCP y agentes

Labs sobre el **Model Context Protocol (MCP)**: cómo exponer herramientas a un modelo (Claude Desktop o Claude Code) y cómo combinar varios servidores MCP en un mismo flujo de trabajo.

| Lab | Qué aprendes | Cómo correrlo |
|---|---|---|
| [lab03-mcp-puppeteer](lab03-mcp-puppeteer/) | Crear un servidor MCP con `@modelcontextprotocol/sdk` (Node.js + TypeScript) que expone `open_url`, `get_page_text` y `screenshot` sobre Chromium headless; registrar el servidor oficial `@playwright/mcp` | `npm install`, `npm run build` y registrar en `.mcp.json` (ver `INSTRUCCIONES.md`) |
| [lab04-kohi-multi-mcp](lab04-kohi-multi-mcp/) | Orquestar 3 MCPs (GitHub, SQLite y Playwright) para construir y probar una web | Ver `INSTRUCCIONES.md` (setup de cada MCP) |

**Orden sugerido:** lab03 (crear un MCP) → lab04 (usar varios MCPs juntos).

**Relación con otras áreas:** los agentes con herramientas propias en Google Cloud están en [lab11-terraform-gcp · micro lab 14 (ADK)](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/14-genai-agent-adk/) y en [lab08-curso-ia](../04-ia-generativa/lab08-curso-ia/) (agentes y multi-agente).
