# Claude-Dev · Learning Labs

Laboratorios prácticos organizados por **área**. Cada lab es un proyecto autocontenido: tiene su propio README, dependencias, configuración de ejemplo y, cuando aplica, pruebas y pipeline de CI.

```
Claude-Dev/
├── 01-desarrollo-web/            Apps web y APIs (Python)
├── 02-mcp-y-agentes/             Servidores MCP y automatización con Claude
├── 03-cloud-e-infraestructura/   Kubernetes, SAP, Terraform en AWS y GCP
├── 04-ia-generativa/             Gemini, RAG, agentes y curso de IA
├── docs/                         Estructura del repo, convenciones y rutas de aprendizaje
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
| | [lab10-terraform-aws](03-cloud-e-infraestructura/lab10-terraform-aws/) | 12 micro labs de AWS: serverless, eventos, GenAI (Bedrock), 3 niveles, SRE, migración, gobernanza | Terraform, AWS, GitLab CI | Intermedio-avanzado |
| | [lab11-terraform-gcp](03-cloud-e-infraestructura/lab11-terraform-gcp/) | 17 micro labs de GCP, incluidos 5 de GenAI (RAG, Vertex AI Search, ADK, Model Armor, tuning) | Terraform, Google Cloud, Vertex AI | Intermedio-avanzado |
| [IA generativa](04-ia-generativa/) | [lab07-rag-vertex-cloudrun](04-ia-generativa/lab07-rag-vertex-cloudrun/) | Chat con RAG sobre documentos propios, desplegable en Cloud Run | FastAPI, Vertex AI Gemini, Terraform | Intermedio |
| | [lab08-curso-ia](04-ia-generativa/lab08-curso-ia/) | Curso de 21 micro labs: fundamentos de IA a agentes en GCP | Python, Vertex AI, ADK, BigQuery | Inicial a avanzado |
| | [lab09-gemini-sdk-basico](04-ia-generativa/lab09-gemini-sdk-basico/) | Primeros scripts con el SDK `google-genai` | Python, Gemini API | Inicial |

## ¿Por dónde empiezo?

| Si quieres... | Empieza en |
|---|---|
| Prepararte como **AI Engineer en Google Cloud** | [Ruta de IA generativa](docs/RUTAS-DE-APRENDIZAJE.md#ruta-1-ai-engineer-en-google-cloud) → lab09 → lab08 → lab07 → lab11 (micro labs 12-16) |
| Aprender **cloud, Terraform y SRE** | [Ruta cloud/DevOps](docs/RUTAS-DE-APRENDIZAJE.md#ruta-2-cloud-devops-y-sre) → lab05 → lab10 → lab11 |
| Construir **backends y apps web** | [Ruta backend](docs/RUTAS-DE-APRENDIZAJE.md#ruta-3-backend-y-aplicaciones-web) → lab01 → lab02 |
| Trabajar con **MCP y Claude** | lab03 → lab04 |
| Entender cómo está organizado el repo o agregar un lab | [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md) |

## Convenciones

- **Cada lab es independiente:** entra a su carpeta y sigue su `README.md`. Las dependencias viven dentro del lab (`requirements.txt`, `package.json`) y cada uno usa su propio entorno virtual.
- **Nombres:** `NN-area/labNN-tema`. El número del lab indica el orden en que se creó; el área agrupa por tema.
- **Secretos:** nunca en el repo. Cada lab trae `.env.example` o `terraform.tfvars.example`; los valores reales van en archivos ignorados por Git o en variables de CI.
- **CI:** cada workflow de `.github/workflows/` se dispara solo con cambios en la carpeta de su lab.

| Workflow | Lab | Qué valida |
|---|---|---|
| `lab2-ci.yml` | lab02 | Lint, tests de Django y build de Docker |
| `lab6-sap-pipeline.yml` | lab06 | Sizing, Terraform y Ansible; despliegue manual |
| `lab8-ci.yml` | lab08 | Lint, tests, quality gate de evaluación y Terraform |
| `lab10-lab11-terraform.yml` | lab10 y lab11 | `terraform fmt`/`validate`, scripts y código Python |

Más detalle en [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md).
