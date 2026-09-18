# Instrucciones — Laboratorio 4 (Kōhi: GitHub + SQLite + Playwright MCP)

Guía paso a paso para dejar los 3 servidores MCP de este lab operativos,
y bitácora de lo que ya se hizo en esta sesión antes de tocar código.
Para el plan completo (qué construye Kōhi y en qué orden), ver
[`README.md`](README.md); este documento es solo el *cómo* y el *qué ya
pasó*.

## 0. Prerrequisitos

- **Node.js 18+** y **npm** (igual que lab3; nada de Python aquí).
- Una cuenta de **GitHub** con acceso de escritura al repo
  `axelvalenzuela/Claude-Dev` (para crear branch y PR en el paso 7 del
  plan).

## 1. Crear el token de GitHub

El servidor MCP de GitHub (`https://api.githubcopilot.com/mcp/`) se
autentica con un **Personal Access Token**:

1. En GitHub: *Settings → Developer settings → Personal access tokens* →
   crea uno (scope `repo` es suficiente) sobre `axelvalenzuela/Claude-Dev`.
2. Guárdalo como variable de entorno de **usuario** en Windows (no lo
   pegues en ningún archivo del repo):

   ```powershell
   setx GITHUB_PERSONAL_ACCESS_TOKEN "tu_token_aqui"
   ```

3. Abre una terminal **nueva** después de correr `setx` (no hereda la
   variable la que ya tenías abierta).

`lab4/.mcp.json` referencia el token como `${GITHUB_PERSONAL_ACCESS_TOKEN}`
— Claude Code lo expande desde tu entorno al lanzar el servidor. El
token real nunca queda escrito en `.mcp.json` ni se sube a git.

## 2. Conectar los 3 servidores MCP

`lab4/.mcp.json` ya registra los tres:

```json
{
  "mcpServers": {
    "github": { "type": "http", "url": "https://api.githubcopilot.com/mcp/", ... },
    "sqlite": { "command": "npx", "args": ["-y", "@executeautomation/database-server", "kohi.db"] },
    "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@latest"] }
  }
}
```

Pasos:

1. Cierra Claude Code si estaba abierto.
2. Ábrelo de nuevo con `lab4/` como directorio de trabajo (los clientes
   MCP solo leen `.mcp.json` al arrancar).
3. Aprueba los tres servidores cuando te lo pida (o corre `claude mcp
   list` y apruébalos desde ahí).

## 3. Verificar que están conectados

```bash
claude mcp list
```

Debe mostrar `github`, `sqlite` y `playwright` como `✔ Connected`. Si
`github` falla, lo más probable es que la variable de entorno no esté
puesta o la terminal sea anterior al `setx`.

## 4. Bitácora de lo hecho en esta sesión (antes de escribir código)

Todo esto ya está commiteado en la rama `learning-labs` (sin `git push`
todavía):

1. **lab3**: se añadió el servidor oficial `@playwright/mcp` a
   `lab3/.mcp.json` (junto al servidor propio `lab3-browser`) y se probó
   con un flujo real: abrir `example.com`, verificar título, tomar
   screenshot, navegar a `httpbin.org/html` y extraer el primer párrafo.
   Documentado en `lab3/README.md` y `lab3/INSTRUCCIONES.md`.
2. **lab4**: se creó este laboratorio desde cero:
   - `lab4/README.md` — plan completo de Kōhi (8 fases, una por cada
     prompt planeado).
   - `lab4/.mcp.json` — los 3 servidores MCP descritos arriba. Sin
     código de la app todavía.
   - `lab4/INSTRUCCIONES.md` — este documento.
3. **README.md raíz** — se agregó la fila de `lab4/` a la tabla de
   laboratorios.

Nada de la app Kōhi (backend, frontend, base de datos, tests E2E, PR) se
ha implementado aún — eso corresponde a las fases 1-8 del plan en
`README.md`, que se ejecutan una vez los 3 MCP estén conectados
(sección 3 de este documento).

## 5. Siguiente paso

Con los 3 servidores en `✔ Connected`, el siguiente paso es la fase 1
del plan: explorar `axelvalenzuela/Claude-Dev` con el MCP de GitHub
(estructura, branches, último commit) sin hacer cambios todavía.
