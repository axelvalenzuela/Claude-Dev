# Estructura del repositorio

Cómo está organizado Claude-Dev, qué convenciones siguen los labs y cómo agregar uno nuevo.

## Organización por áreas

```
Claude-Dev/
├── README.md                     Catálogo de labs y por dónde empezar
├── docs/
│   ├── ESTRUCTURA.md             Este documento
│   └── RUTAS-DE-APRENDIZAJE.md   Rutas por objetivo (IA, cloud, backend)
├── 01-desarrollo-web/
│   ├── README.md
│   ├── lab01-fastapi-todo/
│   └── lab02-django-gastos-viaje/
├── 02-mcp-y-agentes/
│   ├── README.md
│   ├── lab03-mcp-puppeteer/
│   └── lab04-kohi-multi-mcp/
├── 03-cloud-e-infraestructura/
│   ├── README.md
│   ├── lab05-kubernetes-local/
│   ├── lab06-sap-s4hana-fiori/
│   ├── lab10-terraform-aws/
│   └── lab11-terraform-gcp/
├── 04-ia-generativa/
│   ├── README.md
│   ├── lab07-rag-vertex-cloudrun/
│   ├── lab08-curso-ia/
│   └── lab09-gemini-sdk-basico/
└── .github/workflows/            Un workflow por lab, filtrado por ruta
```

- **Área (`NN-area/`):** agrupa labs del mismo tema; su README compara los labs y sugiere el orden.
- **Lab (`labNN-tema/`):** el número es el orden de creación (no se reutiliza); el tema describe qué se construye.

## Equivalencia con los nombres anteriores

| Antes | Ahora |
|---|---|
| `lab1/` | `01-desarrollo-web/lab01-fastapi-todo/` |
| `lab2/` | `01-desarrollo-web/lab02-django-gastos-viaje/` |
| `lab3/` | `02-mcp-y-agentes/lab03-mcp-puppeteer/` |
| `lab4/` | `02-mcp-y-agentes/lab04-kohi-multi-mcp/` |
| `lab5/` | `03-cloud-e-infraestructura/lab05-kubernetes-local/` |
| `lab6/` | `03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/` |
| `lab7/` | `04-ia-generativa/lab07-rag-vertex-cloudrun/` |
| `lab8_IAcourse/` | `04-ia-generativa/lab08-curso-ia/` |
| `lab9_googleSDK/` | `04-ia-generativa/lab09-gemini-sdk-basico/` |
| `lab10_terraform_aws/` | `03-cloud-e-infraestructura/lab10-terraform-aws/` |
| `lab11_terraform_gcp/` | `03-cloud-e-infraestructura/lab11-terraform-gcp/` |

Al mover los labs se actualizaron los links entre labs, las rutas de los workflows de GitHub Actions, el pipeline de GitLab del lab06 y las rutas y llaves de estado de los pipelines de lab10/lab11. Las rutas *dentro* de cada lab no cambiaron.

> **Estado de Terraform (lab10/lab11):** la llave del estado ahora incluye la ruta nueva (`03-cloud-e-infraestructura/lab10-terraform-aws/<lab>/<env>`). Si ya habías desplegado algo con la ruta anterior, haz `terraform init -migrate-state` con la nueva `key`/`prefix` o destruye primero con la configuración anterior.

## Convenciones de cada lab

| Elemento | Convención |
|---|---|
| `README.md` | Qué construye, stack, cómo correrlo, cómo probarlo y troubleshooting. Es el punto de entrada. |
| Guías extra | `INSTRUCCIONES.md` (paso a paso), `CONCEPTOS.md` (teoría), `ARQUITECTURA.md`, `DESPLIEGUE.md`, `docs/` |
| Dependencias | Dentro del lab: `requirements.txt`, `package.json`, `go.mod`… y un entorno virtual propio (`.venv/`, ignorado) |
| Configuración | `.env.example` / `terraform.tfvars.example` versionados; los archivos reales (`.env`, `terraform.tfvars`) ignorados |
| Tests | `tests/` o `scripts/smoke-test.sh` según el tipo de lab |
| CI | `.github/workflows/<lab>-*.yml` con `paths: ["<area>/<lab>/**"]` y `working-directory` del lab |
| Infraestructura | `infra/` o `terraform/` dentro del lab; nunca estado (`*.tfstate`) en el repo |

## Seguridad del repositorio

- Ninguna credencial en el código: API keys en variables de entorno o Secret Manager; en la nube, identidades sin llaves (OIDC / Workload Identity Federation).
- Antes de hacer commit revisa `git diff --staged` en busca de llaves, tokens o datos personales.
- Los labs que despliegan en la nube indican costos y cómo destruir los recursos.

## Cómo agregar un lab nuevo

1. Elige el área (o crea una nueva `05-...` si ninguna aplica) y el siguiente número libre: `labNN-tema`.
2. Crea la carpeta con al menos:
   ```
   labNN-tema/
   ├── README.md            # objetivo, stack, cómo correr, cómo probar, troubleshooting
   ├── requirements.txt     # o el gestor de dependencias que corresponda
   ├── .env.example         # si necesita configuración
   └── src/ · tests/
   ```
3. Agrega una fila en el README del área y en el [catálogo del README raíz](../README.md#catálogo-de-labs).
4. Si tiene CI, crea `.github/workflows/labNN-ci.yml` con `paths` y `working-directory` del lab.
5. Si conviene, agrégalo a una ruta en [RUTAS-DE-APRENDIZAJE.md](RUTAS-DE-APRENDIZAJE.md).
