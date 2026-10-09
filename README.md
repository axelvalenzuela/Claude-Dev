# Claude-Dev · Learning Labs

Laboratorios prácticos organizados por **área**. Cada lab es un proyecto autocontenido: tiene su propio README, dependencias, configuración de ejemplo y, cuando aplica, pruebas y pipeline de CI.

> **¿Buscas IA generativa, Gemini, Vertex AI, Bedrock o Terraform en AWS/GCP?** Está en la carpeta **[04-ai-engineer-gcp-aws](04-ai-engineer-gcp-aws/)** (antes lab07–lab11). Empieza por su [EMPIEZA-AQUI.md](04-ai-engineer-gcp-aws/EMPIEZA-AQUI.md).

```
Claude-Dev/
├── 01-desarrollo-web/            Apps web y APIs (Python)
├── 02-mcp-y-agentes/             Servidores MCP y automatización con Claude
├── 03-cloud-e-infraestructura/   Kubernetes y SAP
├── 04-ai-engineer-gcp-aws/       IA generativa: Gemini, Vertex AI, Bedrock, RAG, agentes y Terraform
├── docs/                         Estructura del repo y rutas de aprendizaje
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
| [AI Engineer GCP/AWS](04-ai-engineer-gcp-aws/) | [01-python-for-ai](04-ai-engineer-gcp-aws/01-python-for-ai/) | Python desde cero orientado a IA | Python | Inicial |
| | [02-ai-fundamentals](04-ai-engineer-gcp-aws/02-ai-fundamentals/) | Tokens, embeddings y redes neuronales sin nube | Python | Inicial |
| | [03-gemini-sdk](04-ai-engineer-gcp-aws/03-gemini-sdk/) | Gemini API y Vertex AI: safety settings, function calling, grounding, embeddings (incluye el lab9) | google-genai, Vertex AI | Intermedio |
| | [04-vertex-ai-projects](04-ai-engineer-gcp-aws/04-vertex-ai-projects/) | RAG, agentes, evaluación, BigQuery, Cloud Run y gobernanza | Vertex AI, ADK, BigQuery | Avanzado |
| | [05-rag-app-cloud-run](04-ai-engineer-gcp-aws/05-rag-app-cloud-run/) | App RAG desplegada en Cloud Run | Vertex AI, Cloud Run, Terraform | Avanzado |
| | [06-terraform-gcp](04-ai-engineer-gcp-aws/06-terraform-gcp/) | Micro labs de Terraform en Google Cloud | Terraform, GCP | Avanzado |
| | [07-bedrock-sdk](04-ai-engineer-gcp-aws/07-bedrock-sdk/) | Ejemplos de Amazon Bedrock | boto3, Bedrock | Intermedio |
| | [08-terraform-aws](04-ai-engineer-gcp-aws/08-terraform-aws/) | Micro labs de Terraform en AWS | Terraform, AWS | Avanzado |

Los números lab07–lab11 no se reutilizan: su material está en [04-ai-engineer-gcp-aws](04-ai-engineer-gcp-aws/) (ver [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md#material-de-ia-04-ai-engineer-gcp-aws)).

## ¿Por dónde empiezo?

| Si quieres... | Empieza en |
|---|---|
| Construir **backends y apps web** | [Ruta backend](docs/RUTAS-DE-APRENDIZAJE.md#ruta-1-backend-y-aplicaciones-web) → lab01 → lab02 |
| Trabajar con **MCP y Claude** | [Ruta MCP](docs/RUTAS-DE-APRENDIZAJE.md#ruta-2-mcp-y-automatización-con-claude) → lab03 → lab04 |
| Aprender **Kubernetes y plataformas empresariales** | [Ruta infraestructura](docs/RUTAS-DE-APRENDIZAJE.md#ruta-3-infraestructura) → lab05 → lab06 |
| Prepararte como **AI Engineer (GCP/AWS)** | [04-ai-engineer-gcp-aws/EMPIEZA-AQUI.md](04-ai-engineer-gcp-aws/EMPIEZA-AQUI.md) |
| Entender cómo está organizado el repo o agregar un lab | [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md) |

## Rama

Todo vive en una sola rama, **`main`**, separado por carpetas. No hay ramas de trabajo: los commits van directo a `main`.

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
