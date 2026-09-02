# Learning Labs

Repositorio de laboratorios independientes. Cada carpeta `labN/` es un
proyecto autocontenido (su propio código, `requirements.txt`, tests y
entorno virtual).

## Laboratorios

| Lab | Descripción |
|-----|-------------|
| [lab1/](lab1/) | API REST de to-do list con FastAPI + SQLite, panel Streamlit y reporte de actividades por correo. |
| [lab2/](lab2/) | App enterprise de reportes de gastos de viaje (Django + SQLite, vistas basadas en clases): portal por empleado (TAXI/MEAL/FLIGHT/HOTEL) con análisis de PDF, política de $60/día y deadline de envío; panel admin con cláusula de aprobación del CEO y auditoría/trazabilidad de reportes y sesiones. |
| [lab3/](lab3/) | Servidor MCP básico (Node.js + TypeScript, `@modelcontextprotocol/sdk`) que controla Chromium headless vía Puppeteer: expone `open_url`, `get_page_text` y `screenshot` como herramientas MCP para Claude Desktop/Claude Code. |

Para correr un laboratorio, entra a su carpeta y sigue el README de ese
proyecto.
