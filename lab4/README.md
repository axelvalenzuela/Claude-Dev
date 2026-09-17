# Laboratorio 4 — Kōhi: 3 MCPs combinados (GitHub + SQLite + Playwright)

Este lab construye **Kōhi**, la web de una cafetería de especialidad con
lista de espera de inauguración, como ejercicio didáctico para demostrar
el uso combinado de tres servidores MCP en un mismo flujo de trabajo:

- **GitHub MCP** — explorar el repo y gestionar el código (branch, commits, PR)
- **SQLite MCP** — crear la base de datos y verificar los datos que el
  backend escribe
- **Playwright MCP** — tests E2E del flujo de usuario completo

## Stack

Node.js + Express, better-sqlite3, bcrypt, JWT, HTML/CSS vanilla (sin
frameworks), Playwright para tests E2E.

## Plan de trabajo (prompts secuenciales)

Cada paso de abajo corresponde a un turno de trabajo con Claude. Se deja
registrado aquí el plan completo antes de ejecutarlo, para que quede
claro el objetivo didáctico de cada MCP en el flujo.

### 1. Explorar el repo (GitHub MCP)

Usar el MCP de GitHub para explorar el repo: estructura de archivos,
branches y último commit. Solo lectura, sin cambios — establece el
estado antes de añadir nada.

### 2. Plan del proyecto

Proponer estructura de archivos/carpetas, endpoints, páginas HTML
(landing, registro a la waitlist, login, panel privado con posición en
cola) y los tests E2E a cubrir con Playwright. Sin implementar todavía.

### 3. Base de datos (SQLite MCP)

Crear `kohi.db` con la tabla `waitlist`:

```sql
CREATE TABLE waitlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  position INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Insertar un usuario de prueba y confirmar con SELECT. Exclusivamente vía
MCP de SQLite, sin scripts.

### 4. Backend (Express + better-sqlite3)

- `POST /api/register` — hashea password con bcrypt, calcula posición
  (`MAX(position)+1`), guarda en SQLite, devuelve la posición asignada.
- `POST /api/login` — verifica credenciales, devuelve JWT.
- `GET /api/me` — protegido con JWT; devuelve name, email, position y
  total de la waitlist.
- Estáticos servidos desde `public/`.

Sin ORMs. Errores: email duplicado → 409, credenciales inválidas → 401,
campos faltantes → 400. Puerto 3000.

### 5. Frontend (HTML/CSS vanilla)

- `index.html` — landing con "Kōhi", subtítulo, filosofía del café,
  botones "Unirme a la lista" / "Ya tengo cuenta".
- `register.html` — formulario de registro; muestra posición asignada.
- `login.html` — formulario de login.
- `dashboard.html` — saludo, posición en cola, barra de progreso, QR
  ficticio.

Paleta oscura elegante (fondo casi negro, texto claro, acento
dorado/ámbar), tipografía minimalista de aire japonés, `fetch()` para
las llamadas.

### 6. Tests E2E (Playwright MCP)

Flujo completo usando exclusivamente las herramientas del MCP de
Playwright (navigate, click, fill, screenshot...), sin escribir archivos
de test con código:

1. Landing muestra "Kōhi" y los botones de registro/login.
2. Registro de "Ana Barista" (`ana@test.com` / `Test1234`) → verifica
   mensaje con la posición asignada.
3. Login con esas credenciales → redirige al dashboard.
4. Dashboard muestra nombre, posición y QR ficticio.
5. Screenshot del dashboard como evidencia.

### 7. Pull Request (GitHub MCP)

- Crear branch `feat/kohi-waitlist`.
- Subir todos los archivos del proyecto a esa branch.
- Crear PR "feat: add Kōhi waitlist app" explicando qué hace la app, qué
  MCPs se usaron y qué demuestra el proyecto.

Exclusivamente vía MCP de GitHub, sin git local.

### 8. Cierre del ciclo (SQLite MCP)

- `SELECT * FROM waitlist` — todos los usuarios.
- Confirmar que `ana@test.com` existe con su posición.
- Mostrar el schema de la tabla.

Esto demuestra el ciclo completo: Playwright interactuó con el
frontend → Express procesó la request → SQLite almacenó el dato → se
verifica directamente en la DB con el MCP.

## Requisitos pendientes antes de ejecutar

- Configurar el servidor MCP de **GitHub** en este proyecto (no está
  configurado todavía).
- Configurar el servidor MCP de **SQLite** en este proyecto (no está
  configurado todavía).
- El servidor MCP de **Playwright** ya está en `.mcp.json` (raíz del
  repo/lab3) pero necesita aprobarse en cada sesión nueva.
