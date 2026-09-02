# Instrucciones — Laboratorio 3 (MCP + Chromium)

Guía paso a paso para arrancar este lab desde cero, y una chuleta de
comandos comunes de MCP para el día a día. Para el *por qué* de cada
decisión de diseño, ver `docs/ARCHITECTURE.md` y `docs/adr/`; este
documento es solo el *cómo*.

## 0. Prerrequisitos

Ver `requirements.txt` para la lista completa con versiones. En resumen:
**Node.js 18+** (probado en Node 24) y **npm** (viene con Node) — nada de
Python es necesario para este lab, a diferencia de lab1/lab2.

Verifica que ya los tienes:

```bash
node --version
npm --version
```

Si falta alguno, instálalo desde <https://nodejs.org/> (incluye npm) antes
de continuar.

## 1. Primera vez: instalar y compilar

```bash
cd lab3
npm install      # instala dependencias Y descarga Chromium (ver docs/adr/0004)
npm run build     # compila TypeScript (src/) -> JavaScript (dist/)
```

`npm install` tarda más de lo normal la primera vez porque descarga un
build de Chromium (decenas de MB) — es esperado, no un error. Confirma
que terminó bien:

```bash
dir "%USERPROFILE%\.cache\puppeteer\chrome"     # Windows — debe listar una carpeta winXX-<version>
```

Si esa carpeta no aparece, tu npm bloqueó el script de instalación de
Puppeteer — corre `npx puppeteer browsers install chrome` para
descargarlo a mano (más detalle en `docs/ARCHITECTURE.md`, sección
"Solución de problemas").

## 2. Conectar el servidor a Claude Desktop / Claude Code

```bash
copy .mcp.json.example .mcp.json    # Windows (cp en Unix/macOS)
```

`.mcp.json` le dice al cliente MCP cómo lanzar el servidor
(`node dist/server.js`). **Reinicia Claude Desktop/Claude Code** después
de crearlo — los clientes MCP solo leen esta configuración al arrancar.

## 3. Probarlo

En una conversación con Claude (ya con el cliente reiniciado), pide algo
como:

> "Abre example.com y dime qué texto tiene la página."

Claude debería invocar `open_url` y luego `get_page_text` por su cuenta.
Si quieres ver una captura, pide "tómale un screenshot".

## 4. El día a día: comandos comunes

| Quiero... | Comando |
|---|---|
| Instalar dependencias (primera vez o tras un `git pull` que las cambió) | `npm install` |
| Compilar después de editar `src/*.ts` | `npm run build` |
| Compilar y correr en un solo paso | `npm run dev` |
| Correr el servidor ya compilado (lo hace el cliente MCP normalmente, no tú a mano) | `npm start` |
| Ver qué herramientas expone el servidor sin abrir Claude | Ver el snippet de smoke test en `docs/ARCHITECTURE.md` |
| Confirmar que Chromium responde | `npx puppeteer browsers list` |
| Reinstalar Chromium desde cero | `npx puppeteer browsers install chrome` |
| Limpiar builds/dependencias (sin tocar el Chromium cacheado) | `rm -rf node_modules dist` |
| Borrar también el Chromium descargado | `rm -rf "$HOME/.cache/puppeteer"` |

## 5. Modificar o agregar una herramienta MCP

1. Añade la función que hace el trabajo real en `src/tools/browser.ts`
   (o un archivo nuevo en `src/tools/` si no es sobre el navegador).
2. Regístrala en `src/server.ts` con `server.tool(nombre, descripción,
   schemaDeEntrada, handler)` — copia el patrón de `open_url` como
   plantilla (nombre corto en snake_case, descripción de una línea que
   explique cuándo usarla, `zod` para validar los argumentos).
3. `npm run build` y reinicia el cliente MCP para que recoja la nueva
   herramienta (las herramientas se listan una sola vez, al conectar).

## 6. Si algo no funciona

Ver la tabla "Solución de problemas" al final de `docs/ARCHITECTURE.md`
— cubre los cuatro problemas más comunes (Chromium no se descargó, el
servidor "no hace nada" al correrlo a mano, Claude no encuentra las
herramientas, `get_page_text`/`screenshot` devuelven una página vacía).
