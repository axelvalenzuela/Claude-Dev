# 0004 — Chromium empaquetado (`puppeteer`), no un navegador del sistema

**Status:** Accepted

## Context

Para controlar un navegador, Puppeteer se distribuye en dos paquetes:
`puppeteer` (descarga y gestiona su propio build de Chromium como parte
de `npm install`) y `puppeteer-core` (no descarga nada; espera que quien
lo use apunte a un navegador ya instalado en el sistema, vía
`executablePath`). El lab pedía explícitamente "instalación de Chromium"
como parte del resultado, así que la elección entre estos dos paquetes
determina si esa instalación ocurre sola o si queda como un paso manual
aparte.

## Decision

Usar **`puppeteer`** (no `puppeteer-core`), dejando que su script de
`postinstall` descargue un build de Chromium a
`~/.cache/puppeteer/chrome/<versión>/` durante `npm install`.

## Alternatives considered

- **`puppeteer-core` + apuntar a un Chrome/Edge ya instalado en el
  sistema** (`executablePath: "C:/Program Files/.../chrome.exe"`): evita
  descargar un segundo binario de Chromium si el usuario ya tiene un
  navegador Chromium-based instalado, pero convierte "instalar Chromium"
  en un paso manual, específico del sistema operativo, y frágil (la ruta
  cambia entre Windows/Mac/Linux, entre versiones, entre instalaciones
  portátiles vs. de sistema) — justo lo opuesto de lo que se pidió para
  este lab. También acopla el comportamiento del servidor a qué versión de
  Chrome tenga esa máquina en particular, en vez de una versión fija y
  reproducible desde `package.json`.
- **Playwright en vez de Puppeteer**: tiene el mismo modelo (un paquete
  que descarga sus propios navegadores) y habría sido una alternativa
  igualmente válida; se descartó por ser una preferencia arbitraria entre
  dos herramientas equivalentes para este alcance, no por una limitación
  real de Playwright.

## Consequences

- `npm install` en lab3 descarga un binario de decenas de MB — más lento
  y más pesado que una instalación de dependencias típica de Node. Es el
  costo directo de que "instalar Chromium" sea automático.
- El build de Chromium queda en el **cache global del usuario**
  (`~/.cache/puppeteer/`), no dentro de `lab3/node_modules/` — se reusa
  entre proyectos que dependan de la misma versión de Puppeteer, y
  **sobrevive** a un `rm -rf node_modules` (ver "Limpieza" en
  `docs/ARCHITECTURE.md`).
- Si la política de npm del entorno bloquea scripts de `postinstall`
  (`allowScripts`), la descarga automática no ocurre y hay que dispararla
  a mano con `npx puppeteer browsers install chrome` — documentado en el
  README y en la tabla de solución de problemas de
  `docs/ARCHITECTURE.md`.
- La versión de Chromium queda fija a la que `puppeteer@23.11.1` empaqueta
  (`131.0.6778.204` al momento de escribir esto) — actualizar Puppeteer en
  `package.json` es también la forma de actualizar Chromium.
