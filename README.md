# Claude-Dev · Learning Labs

Laboratorios prácticos organizados por **área**. Cada lab es un proyecto autocontenido: tiene su propio README, dependencias, configuración de ejemplo y, cuando aplica, pruebas y pipeline de CI.

> **¿Buscas IA generativa, Gemini, Vertex AI, Bedrock o Terraform en AWS/GCP?** Ese material (antes lab07–lab11) vive ahora en su propio repositorio: **[ai-engineer-gcp-aws](https://github.com/axelvalenzuela/ai-engineer-gcp-aws)**.

```
Claude-Dev/
├── 01-desarrollo-web/            Apps web y APIs (Python)
├── 02-mcp-y-agentes/             Servidores MCP y automatización con Claude
├── 03-cloud-e-infraestructura/   Kubernetes y SAP
├── docs/                         Estructura del repo, ramas y rutas de aprendizaje
└── .github/workflows/            CI de los labs (se ejecuta solo cuando cambia su carpeta)
```

## Catálogo de labs

| Área | Lab | Qué construyes | Stack principal | Nivel |
|---|---|---|---|---|
| [Desarrollo web](01-desarrollo-web/) | [lab01-fastapi-todo](01-desarrollo-web/lab01-fastapi-todo/) | API REST de tareas con panel y reporte por correo | FastAPI, SQLite, Streamlit | Inicial |
| | [lab02-django-gastos-viaje](01-desarrollo-web/lab02-django-gastos-viaje/) | App empresarial de reportes de gastos con aprobaciones, auditoría e infraestructura AWS | Django, Docker, CloudFormation | Intermedio |
| [MCP y agentes](02-mcp-y-agentes/) | [lab03-mcp-puppeteer](02-mcp-y-agentes/lab03-mcp-puppeteer/) | Servidor MCP que controla Chromium (abrir URL, leer, captura) | Node.js, TypeScript, MCP SDK, Puppeteer | Intermedio |
| | [lab04-kohi-multi-mcp](02-mcp-y-agentes/lab04-kohi-multi-mcp/) | Web de cafetería usando 3 MCPs combinados (GitHub, SQLite, Playwright) | MCP, Playwright | Intermedio |
| [Cloud e infraestructura](03-cloud-e-infraestructura/) | [lab05-kubernetes-local](03-cloud-e-infraestructura/lab05-kubernetes-local/) | Objetos básicos de Kubernetes en un clúster local | Kubernetes, kubectl, ingress-nginx | Inicial |
| | [lab06-sap-s4hana-fiori](03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/) | Arquitectura, assessment y automatización de S/4HANA + Fiori | Terraform, Ansible, pipelines | Avanzado |

Los números lab07–lab11 no se reutilizan: corresponden al material que se movió a [ai-engineer-gcp-aws](https://github.com/axelvalenzuela/ai-engineer-gcp-aws) (ver [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md#labs-movidos-a-otro-repositorio)).

## ¿Por dónde empiezo?

| Si quieres... | Empieza en |
|---|---|
| Construir **backends y apps web** | [Ruta backend](docs/RUTAS-DE-APRENDIZAJE.md#ruta-1-backend-y-aplicaciones-web) → lab01 → lab02 |
| Trabajar con **MCP y Claude** | [Ruta MCP](docs/RUTAS-DE-APRENDIZAJE.md#ruta-2-mcp-y-automatización-con-claude) → lab03 → lab04 |
| Aprender **Kubernetes y plataformas empresariales** | [Ruta infraestructura](docs/RUTAS-DE-APRENDIZAJE.md#ruta-3-infraestructura) → lab05 → lab06 |
| Prepararte como **AI Engineer (GCP/AWS)** | Repositorio [ai-engineer-gcp-aws](https://github.com/axelvalenzuela/ai-engineer-gcp-aws) |
| Entender cómo está organizado el repo, sus ramas o agregar un lab | [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md) |

## Ramas

| Rama | Para qué |
|---|---|
| `main` | Versión estable y rama por defecto. Aquí están todos los labs organizados. |
| `develop` | Trabajo en curso. Cuando algo está listo, se integra a `main` con un Pull Request. |

Flujo completo en [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md#ramas-y-flujo-de-trabajo).

## Convenciones

- **Cada lab es independiente:** entra a su carpeta y sigue su `README.md`. Las dependencias viven dentro del lab (`requirements.txt`, `package.json`) y cada uno usa su propio entorno virtual.
- **Nombres:** `NN-area/labNN-tema`. El número del lab indica el orden en que se creó; el área agrupa por tema.
- **Secretos:** nunca en el repo. Cada lab trae `.env.example` o `terraform.tfvars.example`; los valores reales van en archivos ignorados por Git o en variables de CI.
- **CI:** cada workflow de `.github/workflows/` se dispara solo con cambios en la carpeta de su lab.

| Workflow | Lab | Qué valida |
|---|---|---|
| `lab2-ci.yml` | lab02 | Lint, tests de Django y build de Docker |
| `lab6-sap-pipeline.yml` | lab06 | Sizing, Terraform y Ansible; despliegue manual |

Más detalle en [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md).
