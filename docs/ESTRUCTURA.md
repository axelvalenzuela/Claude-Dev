# Estructura del repositorio

Cómo está organizado Claude-Dev, qué ramas tiene, qué convenciones siguen los labs y cómo agregar uno nuevo.

## Organización por áreas

```
Claude-Dev/
├── README.md                     Catálogo de labs y por dónde empezar
├── docs/
│   ├── ESTRUCTURA.md             Este documento
│   └── RUTAS-DE-APRENDIZAJE.md   Rutas por objetivo
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
│   └── lab06-sap-s4hana-fiori/
└── .github/workflows/            Un workflow por lab, filtrado por ruta
```

- **Área (`NN-area/`):** agrupa labs del mismo tema; su README compara los labs y sugiere el orden.
- **Lab (`labNN-tema/`):** el número es el orden de creación (no se reutiliza); el tema describe qué se construye.

## Ramas y flujo de trabajo

El repositorio tiene solo dos ramas:

| Rama | Contenido | Reglas |
|---|---|---|
| `main` | Versión estable; rama por defecto en GitHub | No se trabaja directo aquí: solo recibe Pull Requests desde `develop` |
| `develop` | Trabajo en curso | Aquí haces commits; cuando algo está terminado y validado, abres un PR a `main` |

Flujo diario:

```bash
git switch develop
git pull
# ... trabajas y haces commits ...
git push
# en GitHub: Pull Request develop -> main; al aprobarlo, main queda actualizado
git switch develop && git merge main      # opcional: re-sincronizar develop después del merge
```

Si quieres probar algo grande sin ensuciar `develop`, crea una rama temporal desde `develop` (`git switch -c prueba-x`), intégrala con un PR y **bórrala al terminar** para que siempre queden solo estas dos.

## Labs movidos a otro repositorio

Los labs de IA generativa y Terraform en la nube se movieron a [ai-engineer-gcp-aws](https://github.com/axelvalenzuela/ai-engineer-gcp-aws), un repositorio enfocado en la preparación como AI Engineer en Google Cloud y AWS. Sus números no se reutilizan aquí.

| Antes (Claude-Dev) | Ahora (ai-engineer-gcp-aws) |
|---|---|
| `lab07-rag-vertex-cloudrun` | `05-rag-app-cloud-run` |
| `lab08-curso-ia` parte 0 / parte 1 / parte 2 | `01-python-for-ai` / `02-ai-fundamentals` / `04-vertex-ai-projects` |
| `lab09-gemini-sdk-basico` | `03-gemini-sdk/01-gemini-api-quickstart` |
| `lab10-terraform-aws` | `08-terraform-aws` (y sus ejemplos de SDK en `07-bedrock-sdk`) |
| `lab11-terraform-gcp` | `06-terraform-gcp` (y sus ejemplos de SDK en `03-gemini-sdk/02-vertex-ai-examples`) |

El historial de esos archivos sigue disponible en Git (`git log -- 04-ia-generativa/`).

## Equivalencia con los nombres originales

| Antes | Ahora |
|---|---|
| `lab1/` | `01-desarrollo-web/lab01-fastapi-todo/` |
| `lab2/` | `01-desarrollo-web/lab02-django-gastos-viaje/` |
| `lab3/` | `02-mcp-y-agentes/lab03-mcp-puppeteer/` |
| `lab4/` | `02-mcp-y-agentes/lab04-kohi-multi-mcp/` |
| `lab5/` | `03-cloud-e-infraestructura/lab05-kubernetes-local/` |
| `lab6/` | `03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/` |
| `lab7/`, `lab8_IAcourse/`, `lab9_googleSDK/`, `lab10_terraform_aws/`, `lab11_terraform_gcp/` | Repositorio [ai-engineer-gcp-aws](#labs-movidos-a-otro-repositorio) |

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

1. Elige el área (o crea una nueva `04-...` si ninguna aplica) y el siguiente número libre: `lab12-tema`.
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
6. Trabaja en `develop` y súbelo a `main` con un Pull Request.
