# Learning Labs

Repositorio de laboratorios independientes. Cada carpeta `labN/` es un
proyecto autocontenido (su propio código, `requirements.txt`, tests y
entorno virtual).

## Laboratorios

| Lab | Descripción |
|-----|-------------|
| [lab1/](lab1/) | API REST de to-do list con FastAPI + SQLite, panel Streamlit y reporte de actividades por correo. |
| [lab2/](lab2/) | App enterprise de reportes de gastos de viaje (Django + SQLite, vistas basadas en clases): portal por empleado (TAXI/MEAL/FLIGHT/HOTEL) con análisis de PDF, política de $60/día y deadline de envío; panel admin con cláusula de aprobación del CEO y auditoría/trazabilidad de reportes y sesiones. |
| [lab3/](lab3/) | Servidor MCP básico (Node.js + TypeScript, `@modelcontextprotocol/sdk`) que controla Chromium headless vía Puppeteer: expone `open_url`, `get_page_text` y `screenshot` como herramientas MCP para Claude Desktop/Claude Code. También registra el servidor oficial `@playwright/mcp` para probar navegación/screenshot/verificación de título contra sitios reales. |
| [lab4/](lab4/) | Kōhi: web de una cafetería con lista de espera de inauguración, construida como ejercicio de 3 MCPs combinados — GitHub (explorar repo, branch, PR), SQLite (`kohi.db` vía `@executeautomation/database-server`) y Playwright (tests E2E). En planificación: ver [lab4/README.md](lab4/README.md) para el plan completo y [lab4/INSTRUCCIONES.md](lab4/INSTRUCCIONES.md) para el setup. |

Para correr un laboratorio, entra a su carpeta y sigue el README de ese
proyecto.
