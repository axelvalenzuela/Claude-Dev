# 0005 — Un solo browser/page compartidos, no uno nuevo por llamada

**Status:** Accepted

## Context

Cada una de las tres herramientas (`open_url`, `get_page_text`,
`screenshot`) se invoca como una llamada MCP independiente — el servidor
no recibe ningún contexto de "sigue siendo la misma navegación que antes"
más allá de lo que él mismo decida recordar entre llamadas.
`src/tools/browser.ts` necesitaba decidir si cada llamada abre su propio
`Browser`/`Page` de Puppeteer desde cero, o si el proceso mantiene uno
compartido entre llamadas.

## Decision

Mantener un único `Browser` y una única `Page` como estado del módulo
(`browser`/`page` en `browser.ts`), creados de forma perezosa en la
primera llamada y reutilizados en todas las siguientes, mientras el
proceso del servidor siga vivo.

## Alternatives considered

- **Lanzar un `Browser` nuevo (o al menos una `Page` nueva) en cada
  llamada**: cada herramienta quedaría totalmente aislada de las demás —
  sin posibilidad de que una llamada afecte el estado que otra deja atrás
  — pero rompería el caso de uso principal del lab: `open_url` seguido de
  `get_page_text`/`screenshot` **necesita** ser la misma página para que
  "lee el texto"/"toma la captura" se refiera a la URL que se acaba de
  abrir. Con una página nueva por llamada, `get_page_text` siempre leería
  una página en blanco. También sería notablemente más lento — arrancar
  un proceso de Chromium completo tiene un costo de decenas a cientos de
  milisegundos que una sola llamada a `page.goto()` no tiene.
- **Un pool de páginas, una por "sesión" identificada por el cliente**:
  más cercano a cómo se comportaría un navegador real con pestañas, pero
  el protocolo MCP no le da al servidor un identificador de sesión/
  conversación por defecto en un `tools/call` — habría requerido inventar
  un parámetro de sesión en cada herramienta, complejidad que un lab
  básico de una sola página abierta a la vez no necesita.

## Consequences

- **Todas las llamadas comparten una sola pestaña** — si en el futuro se
  agregara una herramienta para abrir una segunda URL en paralelo, esta
  implementación la sobreescribiría en la misma página en vez de abrir una
  pestaña nueva. No es un problema para las tres herramientas actuales,
  que asumen un flujo secuencial de una sola navegación a la vez.
- **El estado sobrevive entre llamadas, pero no entre reinicios del
  servidor** — si el cliente MCP relanza el proceso (o la máquina se
  reinicia), `browser`/`page` vuelven a ser `undefined` y la próxima
  llamada a `open_url` los recrea desde cero.
- `getPage()` revisa `page.isClosed()` antes de reusarla — si algo externo
  cierra la página (o el propio Chromium crashea), la siguiente llamada la
  vuelve a crear en vez de fallar contra una referencia inválida.
- `closeBrowser()` (llamado en `SIGINT`) es el único punto de apagado
  explícito — sin él, el proceso `chrome.exe` hijo podría quedar corriendo
  después de que el servidor Node termine.
