# Micro lab 02: AWS AppSync (GraphQL) + DynamoDB + suscripciones en tiempo real

> **Objetivo:** exponer una API GraphQL administrada con resolvers JavaScript que acceden **directo** a DynamoDB (sin Lambda) y suscripciones WebSocket, con autorización por usuario.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~2 min · **Costo si queda encendido:** Free tier

**Prerrequisitos**

- Micro lab 00

**1. Prepara las variables**

```bash
cd 08-terraform-aws
cp microlabs/02-serverless-appsync-graphql/terraform.tfvars.example microlabs/02-serverless-appsync-graphql/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  02-serverless-appsync-graphql
bash scripts/lab.sh plan  02-serverless-appsync-graphql   # revisa qué se crea
bash scripts/lab.sh apply 02-serverless-appsync-graphql
```

**3. Después del apply**

- Prueba también en la consola de AppSync → *Queries* (login con el user pool)

**4. Verifica**

```bash
bash scripts/lab.sh test 02-serverless-appsync-graphql   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 02-serverless-appsync-graphql
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| schema.graphql | Tipos, queries, mutations, directivas de auth | Para nuevos campos |
| resolvers/*.js + `local.resolvers` en main.tf | Un archivo por resolver y su entrada en el mapa | Por cada campo nuevo del schema |
| variables.tf → `query_depth_limit`, `enable_cache` | Protección y caché | Al crecer el tráfico |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
App web/móvil ──JWT Cognito──► AppSync GraphQL API ─── WebSocket (onCreateNote)
                                 │  auth: Cognito (default) + IAM (backend)
                                 │  query_depth_limit, logs ERROR, X-Ray
                                 ▼
                     Resolvers APPSYNC_JS (getNote, listNotes, createNote, deleteNote)
                                 │ rol de servicio (solo tabla notes)
                                 ▼
                     DynamoDB notes  (owner = sub del JWT, id = autoId)
```

## Archivos clave (templates)

| Archivo | Para qué |
|---|---|
| `schema.graphql` | Tipos, directivas de auth `@aws_cognito_user_pools` / `@aws_iam`, `@aws_subscribe` |
| `resolvers/*.js` | Lógica de mapeo request/response a DynamoDB; filtran por `ctx.identity.sub` |
| `main.tf` | API, data source, resolvers (`for_each` sobre `local.resolvers`), caché opcional |

Para agregar un campo nuevo: (1) añádelo al schema, (2) crea `resolvers/<campo>.js`, (3) agrega una entrada en `local.resolvers`.

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `field_log_level` | `ERROR` | `ALL` solo para depuración |
| `query_depth_limit` | 5 | Protección contra queries anidadas abusivas |
| `enable_cache` | `false` | Caché SMALL (~USD 0.044/h) |
| `log_retention_days` | 30 | |

## Pruebas

1. Crea un usuario como en el micro lab 01 (`admin-create-user` + `admin-set-user-password`) y obtén el `IdToken`.
2. Consola de AppSync → *Queries* → login con el user pool, o:
```bash
curl -s $(terraform output -raw graphql_url) -H "Authorization: $TOKEN" -H 'Content-Type: application/json' \
  -d '{"query":"mutation { createNote(input:{title:\"hola\", content:\"aie\"}) { id title createdAt } }"}'
curl -s $(terraform output -raw graphql_url) -H "Authorization: $TOKEN" -H 'Content-Type: application/json' \
  -d '{"query":"{ listNotes(limit:10) { items { id title } nextToken } }"}'
```
3. Abre una suscripción `onCreateNote` en la consola y ejecuta otra mutación para verla llegar en tiempo real.

## Parámetros en GitLab

| Variable | Tipo |
|---|---|
| `AWS02_TFVARS` | File |

**Job opcional de calidad:** `npx @aws-appsync/eslint-plugin` sobre `resolvers/` en la etapa `validate`.

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd 08-terraform-aws
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>   # no aplica al micro lab 00
cp microlabs/02-serverless-appsync-graphql/terraform.tfvars.example microlabs/02-serverless-appsync-graphql/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  02-serverless-appsync-graphql
bash scripts/lab.sh apply 02-serverless-appsync-graphql
bash scripts/lab.sh test  02-serverless-appsync-graphql      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 02-serverless-appsync-graphql
```

Con `make`: `make apply LAB=02-serverless-appsync-graphql` · `make test LAB=02-serverless-appsync-graphql`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Crea **dos** usuarios (A y B) para validar el aislamiento: A crea una nota; B no la ve ni en `listNotes` ni en `getNote`. También valida el 401 sin token, el rechazo de queries más profundas que `query_depth_limit` y el borrado.

### Resultado esperado (extracto)

```
== Mutaciones y consultas
  OK   createNote (8b0e...)
  OK   listNotes (usuario A) contiene la nota (1)
  OK   listNotes (usuario B) NO ve notas de A (0)
  OK   getNote de B sobre nota de A devuelve null (null)
== Seguridad
  OK   Sin token (401)
  OK   Query demasiado profunda rechazada (query_depth_limit)
SMOKE TEST OK  (8 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `The code contains one or more errors` al crear un resolver | Error de sintaxis en `resolvers/*.js`. Valida localmente con `aws appsync evaluate-code --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 --code file://resolvers/getNote.js --function request --context file://ctx.json`. |
| `Unauthorized` en la consola de AppSync | En *Queries* elige el user pool como modo de autorización e inicia sesión con un usuario confirmado. |
| Las suscripciones no llegan | La mutación debe devolver los campos que pide la suscripción (`id`, `title`, ...); AppSync solo envía lo seleccionado en la mutación. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Schema y resolvers versionados en Git; un resolver por archivo |
| Seguridad | Autorización por campo; aislamiento por `owner`; introspection deshabilitada en prod; profundidad limitada |
| Confiabilidad | Servicio administrado multi-AZ; condiciones `attribute_not_exists`/`exists` |
| Eficiencia de rendimiento | Resolvers directos (sin cold starts de Lambda); caché opcional |
| Optimización de costos | Pago por request; sin Lambda intermedia |
| Sostenibilidad | Menos saltos de cómputo por request |

## Storage mínimo

DynamoDB on-demand con PITR; logs de AppSync con retención de 30 días.

## Limpieza

`terraform destroy`
