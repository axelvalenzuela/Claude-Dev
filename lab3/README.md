# Laboratorio 3 — Servidor MCP de automatización web (Chromium)

Servidor **MCP (Model Context Protocol)** básico construido con el SDK
oficial de Anthropic (`@modelcontextprotocol/sdk`) en **Node.js +
TypeScript**. Controla una instancia de **Chromium headless** vía
[Puppeteer](https://pptr.dev/) y expone tres herramientas que un cliente
MCP (Claude Desktop, Claude Code) puede invocar directamente.

> **¿Primera vez aquí?** Sigue [`INSTRUCCIONES.md`](INSTRUCCIONES.md)
> paso a paso. `requirements.txt` lista los prerrequisitos y versiones
> exactas instaladas. Para entender *cómo funciona* (incluida la pregunta
> de si esto es Infraestructura como Código — no lo es, ver por qué) ve a
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); el porqué de cada
> decisión de diseño está en [`docs/adr/`](docs/adr/).

## Por qué este alcance

De los dos enfoques posibles para un lab de MCP con navegador — escribir
un servidor propio, o solo instalar/configurar uno ya publicado (p. ej.
Playwright MCP) — se eligió **escribir el servidor propio**: es lo que deja
ver de verdad cómo se define una herramienta MCP (nombre, descripción,
schema de entrada con `zod`, handler) en vez de tratarlo como una caja
negra ya armada. TypeScript/Node se usó por ser el stack donde vive el SDK
de MCP más maduro y la mayoría de los servidores de referencia, aunque
lab1/lab2 de este repo son Python — este lab documenta esa diferencia
explícitamente en vez de forzar Python solo por consistencia.

## Stack

- **Node.js 24 + TypeScript 5** (`tsc` compila `src/` → `dist/`, sin
  bundler — un lab básico no lo necesita).
- **`@modelcontextprotocol/sdk`**: `McpServer` + `StdioServerTransport` —
  el servidor habla MCP por **stdio**, el transporte que usan Claude
  Desktop y Claude Code al lanzar un servidor local como subproceso.
- **`puppeteer`** (no `puppeteer-core`): a diferencia de `puppeteer-core`,
  el paquete `puppeteer` **descarga su propio build de Chromium** como
  parte de `npm install` (`postinstall` → `node install.mjs`). Esa
  descarga *es* "la instalación de Chromium" para este lab — no hay un
  paso manual aparte, correr `npm install` ya la dispara.
- **`zod`**: valida el schema de entrada de cada herramienta (p. ej.
  `open_url` exige un `url` con formato válido) antes de que el handler
  se ejecute.

## Instalación

```bash
cd lab3
npm install     # instala @modelcontextprotocol/sdk, puppeteer, zod, y
                 # dispara la descarga de Chromium (build de Puppeteer)
npm run build    # compila TypeScript -> dist/
```

**Nota sobre el `postinstall` de Puppeteer**: si tu configuración de npm
tiene restringidos los scripts de instalación
(`npm warn install-scripts ... puppeteer (postinstall: node install.mjs)`),
Chromium no se descarga automáticamente. Verifica primero si ya existe un
build cacheado de una instalación previa:

```bash
# Windows
dir "%USERPROFILE%\.cache\puppeteer\chrome"
```

Si no aparece ninguna carpeta `winXX-<version>`, descarga Chromium
explícitamente con el propio instalador de Puppeteer:

```bash
npx puppeteer browsers install chrome
```

## Herramientas expuestas

| Herramienta | Entrada | Descripción |
|---|---|---|
| `open_url` | `url: string` | Abre la URL en la página de Chromium (crea el browser headless si es la primera llamada). Devuelve `{ title, url }` tras redirecciones. |
| `get_page_text` | *(ninguna)* | Devuelve el texto visible (`document.body.innerText`) de la página actualmente abierta. Requiere haber llamado `open_url` antes. |
| `screenshot` | *(ninguna)* | Devuelve una captura PNG (base64) de la página actualmente abierta. |

El browser y la página son **una sola instancia compartida** entre
llamadas (`src/tools/browser.ts`) — así `open_url` → `get_page_text` →
`screenshot` operan sobre la misma navegación, como haría una persona
usando el navegador, en vez de abrir una pestaña nueva por llamada.

## Probarlo

**Standalone (sin cliente MCP)**: `npm start` deja el servidor esperando
mensajes MCP por stdio — no hace nada visible por sí solo, es para
depurar que arranca sin errores.

**Con un cliente MCP real (Claude Desktop / Claude Code)**: copia
`.mcp.json.example` a `.mcp.json` (o agrega su contenido a tu config de
Claude Desktop) y reinicia el cliente:

```json
{
  "mcpServers": {
    "lab3-browser": {
      "command": "node",
      "args": ["dist/server.js"],
      "cwd": "."
    }
  }
}
```

Luego, en una conversación, pide algo como *"abre example.com y dime qué
texto tiene"* — Claude debería llamar `open_url` seguido de
`get_page_text` por su cuenta.

## Verificación hecha en este lab

Antes de dar el lab por armado se corrieron dos pruebas:

1. **Chromium headless arranca y navega**: `puppeteer.launch({ headless:
   true })` + `page.goto("https://example.com")` — confirma que el build
   de Chromium descargado por `npm install` funciona, no solo que existe
   en disco.
2. **El servidor MCP responde por stdio**: un cliente MCP de smoke-test
   (`@modelcontextprotocol/sdk` `Client` + `StdioClientTransport`) lanzó
   `dist/server.js` como subproceso, listó las 3 herramientas
   (`listTools`) y las invocó una por una (`callTool`) contra
   `https://example.com`, confirmando título, texto y tamaño del
   screenshot en base64 — el mismo flujo que usaría Claude Desktop/Claude
   Code al conectarse.

## Estructura

```
lab3/
  src/
    server.ts          # Define el McpServer, registra las 3 herramientas, conecta stdio
    tools/browser.ts    # Browser/página de Puppeteer compartidos entre llamadas
  docs/
    ARCHITECTURE.md      # Cómo funciona de punta a punta, diagramas, comandos, troubleshooting
    adr/                  # Decisiones de arquitectura (0001-0005), con alternativas y consecuencias
  package.json
  tsconfig.json
  requirements.txt       # Prerrequisitos y versiones instaladas (equivalente informativo a lab1/lab2)
  INSTRUCCIONES.md        # Guía paso a paso + comandos comunes de MCP
  .mcp.json.example      # Config de ejemplo para registrar el server en un cliente MCP
  .gitignore              # node_modules/, dist/
  README.md
```
