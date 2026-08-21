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

- **SQLite por default**: es un archivo (`db.sqlite3` dentro del volumen
  `/data`), no un servicio aparte que administrar, respaldar o parchear
  por separado. Para una herramienta interna de bajo tráfico (reportes de
  viáticos de una empresa, no un servicio público) esto es apropiado — la
  limitación real de SQLite es la concurrencia de **escrituras**
  simultáneas (un escritor a la vez), no de lecturas, y el volumen de uso
  esperado aquí está muy por debajo de donde eso empieza a importar.
- **Cuándo migrar a un motor con servidor** (Postgres, típicamente): si el
  uso crece a varios admins/empleados escribiendo simultáneamente de forma
  frecuente, o si la empresa ya tiene un servidor de base de datos
  corporativo que prefiere usar. El cambio no requiere tocar código: basta
  con definir `DATABASE_URL` en `.env` (sintaxis de `django-environ`, p.
  ej. `postgres://usuario:clave@host:5432/nombre_db`) y agregar el driver
  correspondiente (`psycopg`) a `requirements.txt`. `config/settings.py`
  ya lee esa variable.
- **CPU/RAM del servidor**: nada fuera de lo común — un servidor pequeño
  (1-2 vCPU, 1-2 GB de RAM) es más que suficiente para este volumen de uso;
  la app no hace procesamiento pesado salvo el análisis de texto de PDFs al
  subir un documento, que es puntual y ligero.

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
