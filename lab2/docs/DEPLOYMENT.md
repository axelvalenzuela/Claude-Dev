# Despliegue (servidor de intranet)

Esta app se construyó y se prueba como servidor de desarrollo local. Este
documento cubre cómo queda la infraestructura para correrla en un servidor
de intranet de la empresa, y los pasos para prepararlo. **Antes de este
trabajo nada de esto existía** — no había `Dockerfile`, ni `STATIC_ROOT`, ni
servidor WSGI de producción, ni pipeline de CI. Todo es nuevo.

## Por qué contenedores y no una instalación directa

Para una herramienta interna de este tamaño, correrla como contenedor es la
opción más prudente frente a instalar Python/Django directamente en un
servidor Windows o Linux:

- **Reproducibilidad.** La imagen fija la versión exacta de Python y cada
  dependencia (`requirements.txt`). "En mi máquina funciona" deja de ser un
  problema — el contenedor que pasó CI es el mismo que corre en el
  servidor.
- **Actualizaciones y rollbacks limpios.** Publicar una versión nueva es
  reconstruir la imagen y reiniciar el contenedor; regresar a la anterior
  es correr la etiqueta de imagen previa. No hay un `pip install --upgrade`
  a medias en un servidor vivo que se pueda hacer mal.
- **Aislamiento.** El entorno de Python de la app no puede desalinearse ni
  chocar con lo que TI ya tenga corriendo en ese servidor.
- **Nada de Python que mantener directamente en el servidor.** Solo hace
  falta Docker (o un runtime OCI equivalente); TI no tiene que mantener
  parchada y asegurada por separado una instalación de Python.

El costo es que quien administra el servidor necesita Docker disponible. En
un servidor de intranet de la empresa eso normalmente es una configuración
de una sola vez, así que vale la pena para una herramienta que se va a
volver a desplegar más de una vez.

## Infraestructura

Un único contenedor resuelve toda la app — no hace falta nginx ni un
servidor de aplicación separado en frente, porque WhiteNoise (dentro del
mismo proceso) ya sirve los archivos estáticos:

```
┌──────────────────────────┐        ┌────────────────────────────────────┐
│  Navegador (empleados y   │  HTTP  │  Servidor de intranet               │
│  admins), dentro de la    │───────▶│  ┌────────────────────────────┐    │
│  red de la empresa        │  :8000 │  │ Contenedor "web"            │    │
└──────────────────────────┘        │  │ gunicorn + Django + WhiteNoise│   │
                                     │  └───────────────┬────────────┘    │
                                     │                  │ lee/escribe      │
                                     │                  ▼                  │
                                     │  ┌────────────────────────────┐    │
                                     │  │ Volumen "app_data" (/data)  │    │
                                     │  │  db.sqlite3 + media/        │    │
                                     │  └────────────────────────────┘    │
                                     └────────────────────────────────────┘
```

- **Un solo contenedor** (`web` en `docker-compose.yml`): corre `gunicorn`
  (servidor WSGI de producción) sirviendo Django, con WhiteNoise sirviendo
  los archivos estáticos (CSS/JS/Bootstrap vendorizado) desde el mismo
  proceso.
- **Un volumen con nombre** (`app_data`, montado en `/data` dentro del
  contenedor): ahí viven la base de datos SQLite y los archivos subidos/
  generados (`media/`). Al estar fuera del código de la app, un rebuild o
  redeploy nunca los toca.
- **Sin base de datos aparte que administrar**: SQLite es un archivo, no un
  servicio — ver la sección de base de datos más abajo.
- **TLS/HTTPS es opcional y externo** a este contenedor (ver más abajo) —
  `gunicorn` no termina TLS por sí mismo.

## Preparar el ambiente

Requisitos en el servidor de intranet:

1. **Docker Engine** (con el plugin de Compose, que ya viene incluido en
   instalaciones modernas de Docker). Es el único requisito de software —
   no se necesita Python, pip, ni ninguna dependencia de la app instalada
   directamente en el servidor.
2. **Acceso a la red interna** en el puerto que se vaya a usar (por
   default, 8000) desde donde los empleados vayan a acceder.
3. **Espacio en disco**: la imagen es del orden de unos cientos de MB; los
   datos (SQLite + archivos subidos/generados) crecen con el uso pero para
   una herramienta interna de este tipo no se esperan tamaños grandes —
   unos pocos GB son un margen cómodo para empezar.
4. Copiar el repositorio al servidor (`git clone`, o copiar el directorio
   `lab2/` si no se quiere exponer el repo completo).

## Instalación de dependencias

**En el contenedor (cómo se despliega): automática.** El `Dockerfile` ya
instala todo (`pip install -r requirements.txt`, incluyendo `gunicorn` y
`whitenoise`) como parte del build de la imagen — no hay un paso manual de
"instalar dependencias" separado en el servidor; sucede solo al correr
`docker compose up --build`.

**Fuera de un contenedor (solo si en algún momento se corre directo en una
máquina, sin Docker):** los mismos pasos que en desarrollo local — ver la
sección de instalación en el `README.md` principal (`python -m venv .venv`,
`pip install -r requirements.txt`). No es la ruta recomendada para el
servidor (ver la sección de arriba sobre por qué contenedores), pero el
`requirements.txt` es el mismo en ambos casos.

## Levantarlo

1. Con Docker ya instalado en el servidor:
2. Copiar `.env.example` a `.env` junto a `docker-compose.yml` y llenarlo
   con valores reales — como mínimo, un `DJANGO_SECRET_KEY` fuerte y
   aleatorio (el valor por default en `.env.example` es un placeholder de
   desarrollo local y no debe usarse en ningún lugar accesible por nadie
   más que uno mismo) y `DJANGO_ALLOWED_HOSTS` con el hostname/IP de
   intranet del servidor.
3. `docker compose up -d --build`
4. La app queda en `http://<servidor>:8000/`. Las tres cuentas sembradas
   desde `.env` (admin de RH, admin de ICS, admin de arranque) funcionan
   igual que en local — ver la tabla de credenciales del `README.md`
   principal.
5. Para actualizar tras un cambio de código: `git pull && docker compose up -d --build`.
6. Para respaldar: respaldar el volumen `app_data` de Docker (ahí vive la
   base de datos SQLite y cada archivo subido/generado) — p. ej.
   `docker run --rm -v lab2_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app_data.tar.gz -C /data .`

## Características del servidor — base de datos

**Decisión: SQLite para intranet/desarrollo, PostgreSQL para nube o alto
uso** (el razonamiento completo, con alternativas consideradas, está en
[`docs/adr/0002-database-sqlite-then-postgres.md`](adr/0002-database-sqlite-then-postgres.md)).
Resumen:

- **SQLite por default**: es un archivo (`db.sqlite3` dentro del volumen
  `/data`), no un servicio aparte que administrar, respaldar o parchear
  por separado. Para una herramienta interna de bajo tráfico (reportes de
  viáticos de una empresa, no un servicio público) esto es apropiado — la
  limitación real de SQLite es la concurrencia de **escrituras**
  simultáneas (un escritor a la vez), no de lecturas, y el volumen de uso
  esperado aquí está muy por debajo de donde eso empieza a importar. **Esto
  aplica al servidor de intranet de este documento** — un solo contenedor,
  un solo volumen persistente. No aplica igual en la nube (ver más abajo).
- **Cuándo migrar a un motor con servidor** (Postgres, típicamente): si el
  uso crece a varios admins/empleados escribiendo simultáneamente de forma
  frecuente, si la empresa ya tiene un servidor de base de datos
  corporativo que prefiere usar, o **siempre que se despliegue en un
  proveedor de nube** (ver la sección de abajo — ahí deja de ser opcional).
  El cambio no requiere tocar código de la app: basta con (1) agregar
  `psycopg[binary]` a `requirements.txt` (no está instalado por default,
  ya que el default es SQLite) y (2) definir `DATABASE_URL` en `.env`
  (sintaxis de `django-environ`, p. ej.
  `postgres://usuario:clave@host:5432/nombre_db`). `config/settings.py` ya
  lee esa variable — `DATABASES` está armado para aceptar cualquiera de
  los dos motores sin modificarse.
- **CPU/RAM del servidor**: nada fuera de lo común — un servidor pequeño
  (1-2 vCPU, 1-2 GB de RAM) es más que suficiente para este volumen de uso;
  la app no hace procesamiento pesado salvo el análisis de texto de PDFs al
  subir un documento, que es puntual y ligero. Igual de cierto en un
  contenedor en la nube — el tamaño de cómputo no es lo que cambia ahí,
  ver abajo.

## Desplegar en un proveedor de nube (Azure / AWS / GCP)

Todo lo de arriba asume un servidor de intranet: un contenedor siempre
encendido, con un volumen persistente propio. La misma imagen de Docker
(`Dockerfile`) puede correr en Azure, AWS o GCP — pero un proveedor de
nube típicamente rompe dos supuestos que el setup de intranet da por
sentados, y agrega un tercero (secretos). Ninguno requiere rehacer la
app; sí requieren decisiones y, en el caso de los archivos, un cambio de
código real (no solo de configuración) antes de desplegar así en serio.

1. **Base de datos: SQLite deja de ser viable, no solo "no ideal".** La
   mayoría de las plataformas de contenedores administradas (Azure
   Container Apps, AWS App Runner/Fargate, GCP Cloud Run) usan
   almacenamiento efímero o no compartido entre instancias — un redeploy,
   un reinicio, o escalar a 2+ instancias puede perder o corromper un
   archivo SQLite (no hay un solo disco compartido garantizado como el
   volumen Docker del servidor de intranet). Usar una base de datos
   administrada (Postgres) pasa de ser "cuándo migrar" a **requisito**
   antes de desplegar en cualquiera de los tres. Ver
   `docs/adr/0002-database-sqlite-then-postgres.md`.
2. **Almacenamiento de archivos: `media/` en disco local tampoco
   sobrevive.** Los recibos subidos y los Excel/Word generados
   (`media/uploads/`, `media/reports/`) hoy se guardan en disco local —
   funciona en el servidor de intranet (volumen persistente dedicado),
   pero en la mayoría de plataformas de contenedores en la nube el disco
   local es efímero o no se comparte entre instancias, igual que con
   SQLite. **Esto sí es un cambio de código, no solo de infraestructura**:
   agregar `django-storages` con el backend correspondiente (Azure Blob,
   S3, o GCS) y apuntar `DEFAULT_FILE_STORAGE`/`MEDIA_URL` a ese bucket en
   vez de al disco — no implementado todavía en este repo. Sin ese
   cambio, la app solo es segura en la nube corriendo como una única
   instancia con un disco persistente montado (posible en algunas
   plataformas, pero ya no es el patrón idiomático de contenedores en la
   nube).
3. **Secretos fuera de `.env`**: `.env` nunca debe hornearse en la imagen
   ni commitearse (ya es así, ver `.gitignore`) — en la nube, en vez de un
   archivo en el servidor, se usa el gestor de secretos nativo de la
   plataforma (Key Vault / Secrets Manager / Secret Manager, ver tabla
   abajo), inyectado como variables de entorno al desplegar.
   `DJANGO_SECRET_KEY`, las credenciales de la base de datos, y cualquier
   password real de las cuentas admin sembradas (ver la tabla de
   credenciales del `README.md`) necesitan ese tratamiento para cualquier
   cosa más allá de una demo.
4. **HTTPS**: mismo principio que en el servidor de intranet
   (`DJANGO_HTTPS_ENABLED=True` + `DJANGO_CSRF_TRUSTED_ORIGINS`), pero en
   la nube el reverse proxy normalmente es el balanceador/ingress
   administrado de la plataforma (no se corre nginx/Caddy propio en un
   contenedor aparte).
5. **Escalado horizontal**: una vez con Postgres administrado y
   almacenamiento de objetos en su lugar, esta misma imagen puede correr
   más de una instancia sin los problemas de arriba — aunque para el
   volumen de uso real de esta herramienta (viáticos de una empresa, no
   un servicio público) una sola instancia siempre encendida ya es
   suficiente; escalar horizontalmente es una opción disponible, no una
   necesidad actual.
6. **El auto-apagado a las 12h no aplica aquí**: `accounts/
   server_lifecycle.py` (`AUTO_SHUTDOWN_HOURS`) solo se activa bajo
   `manage.py runserver` (ver el código) — en producción corre `gunicorn`
   (este mismo `Dockerfile`, en cualquiera de los tres proveedores), así
   que no hay nada que ajustar por este punto al desplegar en la nube.

**Equivalencias entre los tres proveedores**, para lo que este proyecto
específicamente necesitaría (ninguno es "mejor" en abstracto para esta
app — la decisión real suele depender de dónde la empresa ya tenga
cuentas/contratos, no de una diferencia técnica relevante aquí):

| Necesidad | Azure | AWS | GCP |
|---|---|---|---|
| Correr el contenedor | Container Apps / App Service | ECS Fargate / App Runner | Cloud Run |
| Base de datos administrada | Azure Database for PostgreSQL | RDS for PostgreSQL | Cloud SQL for PostgreSQL |
| Almacenamiento de objetos (`media/`, requiere agregar `django-storages`) | Blob Storage | S3 | Cloud Storage |
| Secretos | Key Vault | Secrets Manager | Secret Manager |
| Registry de imágenes | Azure Container Registry | ECR | Artifact Registry |
| TLS / balanceo | Application Gateway / Front Door | Application Load Balancer | HTTPS Load Balancer |

Lo que es igual en las tres: la imagen de `Dockerfile` que ya existe es
el punto de partida en cualquiera de ellas — el trabajo real está en (1)
apuntar `DATABASE_URL` a Postgres administrado, (2) agregar soporte de
almacenamiento de objetos para `media/` (código nuevo), y (3) mover
secretos del `.env` local al gestor de secretos de la plataforma elegida.

## HTTPS

`gunicorn` no termina TLS por sí mismo. Dos opciones soportadas:

- **Quedarse en HTTP plano** para un primer despliegue interno — es el
  comportamiento por default. Dejar `DJANGO_HTTPS_ENABLED` sin definir
  (`False`).
- **Poner un reverse proxy en frente** (nginx, Caddy, o el balanceador de
  intranet que ya tenga la empresa) que termine TLS y reenvíe al puerto
  8000, y entonces sí poner `DJANGO_HTTPS_ENABLED=True` en `.env`. Esto
  activa juntos `SECURE_SSL_REDIRECT`, cookies seguras y HSTS (ver
  `config/settings.py`) — deliberadamente todo o nada, porque HSTS sin TLS
  real solo bloquearía el acceso.

Si se agrega un reverse proxy, también hay que definir
`DJANGO_CSRF_TRUSTED_ORIGINS` con la(s) URL(s) pública(s) por las que se
accede (p. ej. `https://viaticos.intranet.mhp.local`).

## Política de retención de archivos (90 días)

Los archivos originales de un reporte se borran automáticamente al
aprobarlo (ver README, sección "Excel + Word al aprobar"). Para un reporte
que nunca se aprueba (se queda pendiente, o se rechaza), el comando
`cleanup_old_documents` borra el archivo original una vez que lleva más de
90 días subido (`FILE_RETENTION_DAYS` en `expenses/policies.py`) — el
registro en la base de datos y el reporte en sí **no** se tocan, solo el
archivo.

Este comando **no se ejecuta solo** — hay que programarlo:

```bash
# Dentro del contenedor / entorno con el venv activo:
python manage.py cleanup_old_documents           # borra
python manage.py cleanup_old_documents --dry-run # solo muestra qué borraría
```

- **Linux (cron)**, una vez al día es suficiente:
  ```
  0 3 * * * cd /ruta/al/proyecto && /ruta/al/venv/bin/python manage.py cleanup_old_documents >> /var/log/mhp-cleanup.log 2>&1
  ```
- **Windows (Task Scheduler)**: crear una tarea que ejecute
  `python.exe manage.py cleanup_old_documents` con el directorio de trabajo
  apuntando a `lab2/` y el intérprete del venv del proyecto, programada
  diaria.
- **Contenedor Docker**: si se despliega con `docker-compose.yml`, se puede
  agregar un segundo servicio (o un `cron` dentro de la imagen) que corra
  `docker compose exec web python manage.py cleanup_old_documents` con la
  misma cadencia.

## Pipeline de CI

`.github/workflows/lab2-ci.yml` corre en cada push/PR que toque `lab2/`:
instala dependencias, corre `manage.py check`, corre toda la suite de
tests, corre `manage.py check --deploy` bajo configuración similar a
producción (detecta regresiones de configuración, como una variable de
entorno olvidada, antes de que lleguen al servidor), y hace un
`docker build` para confirmar que la imagen sigue construyéndose. Es una
plantilla inicial — los comentarios al principio de ese archivo listan lo
siguiente que valdría la pena agregar (un linter, un escaneo de
vulnerabilidades de dependencias, publicar la imagen construida en un
registry del que el servidor la descargue) una vez que el equipo decida
esas herramientas.
