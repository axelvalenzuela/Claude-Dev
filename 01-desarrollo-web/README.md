# 01 · Desarrollo web

Aplicaciones web y APIs en Python, de un CRUD sencillo a una aplicación empresarial con flujos de aprobación, auditoría e infraestructura como código.

| Lab | Qué aprendes | Cómo correrlo |
|---|---|---|
| [lab01-fastapi-todo](lab01-fastapi-todo/) | API REST con FastAPI, validación con Pydantic, SQLite sin ORM, panel Streamlit, tests con pytest | `pip install -r requirements.txt` y `uvicorn` (ver su README) |
| [lab02-django-gastos-viaje](lab02-django-gastos-viaje/) | Django con vistas basadas en clases, roles y permisos, análisis de PDF, reglas de negocio (política de $60/día, fechas límite), auditoría, Docker y CloudFormation (ADRs en `docs/adr` e `infra/docs/adr`) | `docker compose up` o entorno virtual (ver su README) |

**Orden sugerido:** lab01 (fundamentos de API) → lab02 (aplicación completa).

**Relación con otras áreas:** el lab02 incluye infraestructura AWS con CloudFormation; para Terraform y arquitecturas de referencia continúa con el módulo [08-terraform-aws](../04-ai-engineer-gcp-aws/08-terraform-aws/) del área 04.
