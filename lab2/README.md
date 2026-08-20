# Laboratorio 2 — MHP by Porsche · Travel Expense Reports

Aplicación web para que cada empleado suba sus documentos de viaje (vuelos,
hoteles, taxis, comidas...), arme un reporte de gastos y lo envíe a revisión.
El reporte se aprueba (o rechaza) por el admin del **departamento** del
empleado, o por el admin general de **RH**; el empleado ve el resultado en
su propio portal. Cualquiera de los dos roles puede descargar el reporte en
Excel. Toda aprobación final queda sujeta a la cláusula de autoridad
delegada del CEO, **Steffan Widmer**.

> La interfaz de la aplicación está **en inglés** (plataforma "enterprise"
> orientada a un equipo internacional); esta documentación queda en español
> para el equipo que la mantiene. Todos los comentarios en el código
> (`.py`) están en inglés.
>
> Se evaluó inicialmente hacerlo en .NET/C#, pero por restricciones de
> permisos en el equipo de desarrollo se implementó en **Python + Django**.

## Marca "MHP by Porsche"

El header de ambas interfaces (portal del empleado y panel admin) lleva el
wordmark **MHP by Porsche**. Se decidió construirlo como un tratamiento
tipográfico en CSS (negro/rojo, la paleta de marca de Porsche) en vez de
descargar e incrustar el logo oficial real: un logo con derechos de autor
metido dentro del repo de git (que además queda en el historial para
siempre) es un riesgo de marca registrada innecesario para un proyecto de
laboratorio — el resultado visual es igual de distintivo sin ese riesgo. Si
más adelante quieres el logo oficial, lo más seguro es enlazarlo desde un
recurso interno propio de la empresa, no incrustarlo en el repo.

## Stack

- **Python 3.13 + Django 5**, vistas **basadas en clases** (`ListView`,
  `CreateView`, `DetailView`, `View` + mixins) en lugar de funciones sueltas.
- **SQLite** vía el ORM de Django (`db.sqlite3`, cero dependencias externas).
- **django-environ**: configuración y secretos vía `.env` (nunca hardcodeados
  en `settings.py`).
- **Django Admin** como panel de administrador — es la forma idiomática de
  dar acceso restringido (`is_staff`) a una sola cuenta para aprobar/rechazar,
  con auditoría de sesiones y de reportes integrada.
- **openpyxl** para generar los reportes `.xlsx`.
- **pypdf** para el análisis best-effort del contenido de los PDF subidos.
- Test framework de Django (basado en `unittest`): **84 tests**.

## Buenas prácticas de instalación de dependencias

- **Versiones fijas** en `requirements.txt` (`==`, no rangos abiertos) para
  builds reproducibles. Para actualizar: instalar la nueva versión, correr
  toda la suite de tests, y solo entonces regenerar el archivo.
- **Entorno virtual por laboratorio** (`lab2/.venv`, no compartido con otros
  labs ni con el sistema) — evita colisiones de versiones entre proyectos.
- **Secretos fuera del código**: `settings.py` lee `SECRET_KEY`, `DEBUG` y
  los datos de la cuenta admin sembrada desde variables de entorno (`.env`,
  gitignored). Se versiona `.env.example` con los nombres de variable y
  valores de desarrollo, nunca `.env` real.
- **Nunca `pip install` sin activar el venv primero** — confirmar con
  `where python` (Windows) / `which python` (Unix) que apunta a
  `lab2/.venv/...` antes de instalar.

```bash
cd lab2
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env        # Windows (cp en Unix) — ajustar si hace falta
python manage.py migrate      # crea la BD y siembra la cuenta admin
python manage.py runserver 8080
```

La app queda disponible en `http://127.0.0.1:8080/`:
- `/accounts/signup/` — crear cuenta de empleado
- `/accounts/login/` — iniciar sesión
- `/reports/` — portal del empleado (redirige aquí tras login)
- `/admin/` — panel de administrador (solo la cuenta sembrada)

### Cuentas admin (sembradas automáticamente)

Tres cuentas con acceso a `/admin/`, cada una representando un rol distinto
del organigrama:

| Rol | Correo | Password | Alcance |
|---|---|---|---|
| Admin general (RH) | `iris.cortez@mhp.com` | `Iris#2026Local` | **Iris Cortez** — ve y aprueba reportes de **todos** los departamentos (`is_superuser`). Es la aprobadora final por defecto. |
| Admin de departamento (ICS) | `adrian.heymes@mhp.com` | `Adrian#2026Local` | **Adrian Heymes** — ve y aprueba **solo** reportes de empleados con `department="ICS"`. |
| Bootstrap (dev) | `axel.valenzuela@uabc.edu.mx` | `Admin#2026Local` | Cuenta genérica de arranque local, configurable vía `ADMIN_SEED_*`; independiente del organigrama. |

Un empleado de ICS (p. ej. tú, registrado con `department="ICS"`) solo
aparece en la bandeja de aprobación de **Adrian Heymes**; **Iris Cortez**
ve ese mismo reporte y el de cualquier otro departamento, porque es la
admin general. Ver la sección de "Roles de administrador" más abajo.

> Contraseñas de desarrollo local únicamente. Cámbialas editando `.env` (o
> las variables `HR_ADMIN_*` / `ICS_ADMIN_*` / `ADMIN_SEED_*` antes del
> primer `migrate`) si vas a correr esto fuera de tu máquina.

### El servidor local se apaga solo a las 12 horas

`python manage.py runserver` arma un timer en segundo plano
(`accounts/server_lifecycle.py`) que termina el proceso automáticamente
después de `AUTO_SHUTDOWN_HOURS` (default: **12**, configurable en `.env`).
Es solo para evitar dejar un servidor de desarrollo corriendo indefinidamente
en tu máquina — no aplica a `test`, `migrate`, `shell`, etc., y no interfiere
con el auto-reload de Django (el timer se arma una sola vez, en el proceso
que realmente atiende peticiones). Para desactivarlo, pon
`AUTO_SHUTDOWN_HOURS=0` en `.env`.

## Módulos implementados

### 1. Cuentas de usuario y trazabilidad de sesiones (`accounts/`)
- Modelo `User` propio (`AUTH_USER_MODEL = "accounts.User"`), agrega
  `department`. El username es el correo.
- **Sign up** (`SignUpView`, CBV `CreateView`): cualquiera crea una cuenta de
  empleado. Nunca queda con `is_staff`/`is_superuser`.
- **Log in / Log out** con el sistema de sesiones de Django.
- **`LoginEvent`**: cada intento de login (exitoso o fallido) se registra vía
  las señales `user_logged_in` / `user_login_failed` de Django
  (`accounts/signals.py`), con usuario (si aplica), correo intentado, IP,
  user agent y fecha. Registrado en Django Admin **de solo lectura** — es el
  marco de referencia de seguridad que pediste: quién entró, cuándo, desde
  dónde, y quién falló al intentarlo.

### 2. Portal del empleado (`expenses/views.py` — vistas basadas en clases)
- `ReportListView`, `ReportDetailView` (con `LoginRequiredMixin`), y
  `UploadDocumentView` / `DeleteDocumentView` / `SubmitReportView` /
  `ExportExcelView` / `DownloadDocumentView` como `View` con un
  `OwnedReportMixin` compartido que garantiza que un empleado **solo puede
  ver/tocar sus propios reportes** (404 en cualquier otro caso).
- **Crear reporte con adjuntos y preview en vivo** (`ReportCreateView` +
  `PreviewDocumentView`, `/reports/new/`): en la misma pantalla donde se
  captura título/descripción/supervisor, se pueden adjuntar **varios PDFs y
  fotos a la vez** (`<input type="file" multiple>`). Cada PDF adjuntado se
  envía por AJAX (`fetch`) al instante a `PreviewDocumentView`
  (`/reports/preview-document/`), que corre el mismo análisis de PDF y
  responde con el monto y tipo detectados — la fila de ese documento se
  autocompleta con esa sugerencia (editable) antes de guardar nada, así el
  empleado puede revisar y corregir antes de decidir crear/enviar el
  reporte. Las fotos (JPG/PNG) no se analizan (no hay texto que leer);
  solo piden tipo/fecha/monto manuales. Al enviar el formulario hay dos
  botones: **Save as draft** (crea el reporte, se puede seguir editando) o
  **Create & submit for review** (crea y envía en un solo paso, quedando
  sujeto a las mismas validaciones de `submit()` — documentos y fecha
  límite). El análisis del lado del servidor (`build_travel_document` en
  `expenses/services.py`, compartido con la subida individual) es siempre
  el que se guarda; el preview del cliente es solo una ayuda visual.
- Documento de viaje: tipo (**TAXI / MEAL / FLIGHT / HOTEL / OTHER**),
  fecha, monto, archivo (PDF/JPG/PNG) — se puede seguir agregando/quitando
  documentos individualmente en el detalle del reporte mientras sigue en
  `draft`.
- **Análisis del PDF al subirlo** (`expenses/pdf_analysis.py`): lee el texto
  del PDF y adivina el monto total y el tipo de gasto por palabras clave
  (`boarding pass`→flight, `hotel/check-in`→hotel, `uber/taxi`→taxi,
  `restaurant/dinner`→meal). Si el monto o el tipo detectado no coincide con
  lo que el empleado capturó, se marca `amount_mismatch` / `type_mismatch` y
  se le avisa — así se evitan errores/posibles incumplimientos de política
  desde el origen, no solo al aprobar.
- **Supervisor**: cada reporte guarda `supervisor_name` (obligatorio) y
  `supervisor_email` (opcional) — a quién queda dirigido el envío. Visible
  en el detalle, en el admin y en el Excel.
- **Enviar a revisión**: exige al menos un documento y respeta la **fecha
  límite de envío** (ver política de deadline abajo).
- **Descarga a Excel** con el desglose diario de gastos.

### 3. Política de $60/día (`ExpenseReport.daily_totals()`)
- Agrupa los documentos por `document_date` y suma el gasto de cada día.
- Cualquier día con total > **$60 USD** se marca `over_limit=True` —
  visible para el empleado (detalle del reporte), para el admin (lista +
  detalle, con ⚠) y en el Excel exportado (fila resaltada en rojo).
- `ExpenseReport.has_policy_violations` resume si el reporte completo tiene
  algún día fuera de política — es la señal de "posible falta a las
  políticas de la empresa" que pediste.

### 4. Fecha límite de envío (fecha de vuelo + 30 días)
- `ExpenseReport.trip_start_date`: la fecha del documento tipo **FLIGHT**
  más antiguo del reporte (o la fecha más antigua entre todos los
  documentos, si todavía no hay ninguno de vuelo).
- `submission_deadline` = `trip_start_date + 30 días` — cubre el caso de un
  viaje de hasta ~2 semanas con margen para armar y enviar el reporte.
- `submit()` **rechaza el envío** si ya pasó la fecha límite, con un mensaje
  claro indicando la fecha límite calculada.

### 5. Documentos deben pertenecer al mismo viaje (`validate_trip_span`)
- Los recibos de un mismo reporte no pueden estar separados por más de
  **`MAX_TRIP_SPAN_DAYS` = 21 días**. Si ya hay documentos de marzo y se
  intenta adjuntar uno de junio, se rechaza con un mensaje claro indicando
  el rango detectado y el límite — exactamente el caso que pediste.
- Se valida en dos puntos: al crear el reporte con varios adjuntos a la vez
  (compara las fechas de todo el lote entre sí) y al agregar un documento
  suelto después (lo compara contra los documentos ya guardados en el
  reporte). Ningún documento se guarda si la validación falla.
- `ExpenseReport.trip_date_range` expone `(fecha_min, fecha_max)` del viaje
  — se muestra en el detalle del reporte, en el admin y en el Excel como
  parte del formato empresarial ("Trip dates: 03/01/2026 – 03/15/2026").

### 6. Límite de páginas por PDF (`pdf_analysis.validate_pdf_page_count`)
- Un recibo de viaje debe tener **máximo 4 páginas**; se rechaza al subirlo
  si tiene más (mensaje claro, no crashea con PDFs corruptos — si no se
  puede leer el número de páginas, no bloquea).
- El análisis de monto/tipo (`analyze_pdf`) **prioriza las primeras 2
  páginas** del PDF — donde casi siempre está el cargo real — y solo
  recurre al resto del documento si no encuentra nada ahí, evitando que un
  número irrelevante de una página posterior (p. ej. un balance de puntos)
  se confunda con el total del gasto.

### 7. Cláusula de aprobación del CEO — Steffan Widmer
- `ExpenseReport.approve(reviewer, note, ceo_clause_ack)` **exige**
  `ceo_clause_ack=True` para aprobar; si no se confirma, lanza error.
- Al aprobar, se graba `ceo_authorized=True` y
  `approval_clause = "Approved under authority delegated by Steffan Widmer, CEO."`,
  visible para el empleado y en el Excel.
- En el admin, esto se ve como un **checkbox obligatorio** ("I confirm this
  approval is issued under the authority of Steffan Widmer (CEO)") que debe
  marcarse para poder guardar una aprobación — rechazar no lo requiere, pero
  sí exige una nota con el motivo.

### 8. Panel de administrador — Django Admin (`expenses/admin.py`)
- Accesible solo para cuentas admin (`is_staff=True`); cualquier empleado
  normal es rechazado por el framework mismo. Con el header, colores y
  hover animations de la marca ("formato empresarial y distintivo" —
  ver `templates/admin/base_site.html` y `static/css/brand.css`).
- **`ExpenseReportAdmin`**: solo reportes ya enviados (los borradores son
  privados del empleado), **ordenados por fecha de envío**
  (`ordering = ["-submitted_at"]`, más reciente primero). Columnas de lista
  incluyen indicador de política ($60/día) y de fecha límite.
- Vista de detalle: desglose diario de gastos con el límite de $60/día
  resaltado, documentos inline (con los campos detectados por el análisis
  de PDF), y el historial de auditoría del reporte inline.
- Aprobar/rechazar reusa las mismas reglas de negocio del modelo
  (`ExpenseReport.approve()`/`reject()`), no las reimplementa.

### 9. Roles de administrador por departamento + notificación de pendientes
- `User.supervised_department`: si se define (p. ej. `"ICS"`), esa cuenta
  admin **solo ve y aprueba** reportes de empleados de ese mismo
  departamento (`ExpenseReportAdmin.get_queryset` filtra por
  `user__department`; intentar abrir el reporte de otro departamento por
  URL directa da 404, no solo se oculta de la lista).
- Una cuenta con `is_superuser=True` (la admin de RH, Iris Cortez) no tiene
  `supervised_department` y ve **todos** los departamentos — es la
  aprobadora general.
- **Notificación "novedades a revisar"**: al entrar a `/admin/`, un banner
  en la parte superior del dashboard muestra cuántos reportes están
  esperando revisión — con el conteo ya filtrado por departamento si quien
  entró es un admin de departamento, o el total si es RH/superusuario.
  Implementado con un context processor
  (`accounts/context_processors.py:pending_reports_notification`) más
  `templates/admin/index.html`, así que usa exactamente la misma lógica de
  alcance que `ExpenseReportAdmin.get_queryset` — nunca pueden quedar
  desincronizados.
- **Organigrama sembrado** (`accounts/migrations/0007_seed_org_admins.py`):
  Iris Cortez (RH, general) y Adrian Heymes (ICS) — ver la tabla de
  credenciales más arriba.

### 10. Retención de archivos de viaje — decisión de buena práctica
Se consideró eliminar los PDFs/fotos de un reporte una vez generado, o
moverlos a un archivo aparte visible solo para el admin. **Se descartó
ambas opciones** a favor de mantenerlos donde ya están (ligados al
`TravelDocument` de su reporte, sin cambios):
- Un sistema de gastos que borra los recibos originales rompe su propio
  propósito: esos archivos son el soporte legal/contable del gasto, y
  deben poder consultarse ante una auditoría o disputa mucho después de
  aprobado el reporte.
- Un "archivo aparte" con capturas duplicaría el almacenamiento sin
  aportar nada — el admin **ya** puede ver todos los recibos de un reporte
  con solo entrar a ese reporte en `/admin/` (inline de documentos con
  liga de descarga), que es exactamente el flujo que se pidió ("simplemente
  tiene que entrar a gestionar el reporte de ese usuario que ya envió").
- Lo único que se automatiza es el *acceso* (el admin correcto ve el
  reporte correcto, ver punto 9) y la *auditoría* (`ExpenseReportAuditLog`,
  punto 12) — no el borrado de evidencia.

### 11. Auditoría e histórico de reportes (`ExpenseReportAuditLog`)
- Registro inmutable (solo lectura en el admin) de cada evento del ciclo de
  vida de un reporte: creado, documento subido, documento eliminado,
  enviado, aprobado, rechazado — con quién (`actor`) y cuándo.
- Se escribe desde las vistas del empleado y desde el admin
  (`ExpenseReportAdmin.save_model`). Es el histórico por usuario que
  pediste, más allá del último estado guardado en `ExpenseReport`.
- Ver [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) para el diagrama de
  relaciones completo y el porqué de este diseño.

### 10. Generación de Excel (`expenses/excel.py`)
- Encabezado con empleado, **número de empleado**, departamento, supervisor,
  **fechas del viaje**, estado y fecha de creación; la cláusula de
  aprobación del CEO si el reporte fue aprobado; la tabla de documentos; y
  el **desglose diario contra la política de $60/día** con las filas fuera
  de límite resaltadas. Formato pensado para verse como un reporte
  corporativo real, no una tabla suelta.

### 11. Documentos y almacenamiento (`expenses/models.py`)
- `TravelDocument.file` valida extensión (`.pdf`, `.jpg`, `.jpeg`, `.png`),
  tamaño máximo (10 MB) y número de páginas (PDFs, máximo 4).
- Nombre físico único (`uuid4`) bajo `media/uploads/{user_id}/{report_id}/`;
  se conserva el nombre original (`original_filename`) para mostrarlo y
  descargarlo.

### 12. Número de empleado (`accounts/models.py`)
- `User.employee_number`: 7 dígitos aleatorios (ej. `2490198`), único,
  asignado automáticamente — nunca lo captura el empleado.
  - Al registrarse (`SignUpForm.save()`), se genera con
    `generate_employee_number()`.
  - Si se crea un usuario desde `/admin/` sin número, `UserAdmin.save_model`
    se lo asigna igual.
  - Los usuarios que ya existían en la base antes de este campo (incluida
    la cuenta admin sembrada) lo reciben mediante una migración de datos
    (`accounts/migrations/0005_backfill_employee_numbers.py`) — "si existe
    gente, ponles un número random", tal como pediste.
- Visible en el admin de usuarios, en el detalle del reporte, en el admin
  de reportes y en el Excel.

## Reglas de negocio (testeadas, `expenses/models.py`)

Viven como métodos del propio modelo `ExpenseReport`, no en las vistas ni en
el admin, para poder probarlas sin pasar por HTTP:

```
draft --submit()--> submitted --approve(ceo_clause_ack=True)--> approved
        (bloqueado si         \-----------reject(note)---------> rejected
         pasó la fecha límite)
```

- `submit()`: exige ≥1 documento, estado `draft`, y no haber pasado la fecha
  límite (fecha de vuelo + 30 días).
- `approve()`: exige estado `submitted` y `ceo_clause_ack=True`.
- `reject()`: exige estado `submitted` y una nota no vacía.
- `validate_trip_span()`: exige que las fechas de los documentos de un mismo
  reporte no se separen por más de 21 días (se corre al crear el reporte
  con adjuntos y al agregar un documento nuevo — nunca al guardar el
  modelo directamente, para no romper reportes ya existentes).

## Estructura

```
lab2/
  manage.py
  .env.example                 # variables de entorno documentadas (copiar a .env)
  docs/DATA_MODEL.md            # diagrama ER y trazabilidad
  config/                       # settings (django-environ, AUTO_SHUTDOWN_HOURS, branding), urls, wsgi/asgi
  accounts/
    models.py                    # User (+ employee_number, supervised_department), LoginEvent
    signals.py                    # graba LoginEvent en cada intento de login
    context_processors.py         # pending_reports_notification (banner "novedades a revisar")
    server_lifecycle.py           # apagado automático del runserver a las 12h
    views.py                      # SignUpView (CBV)
    migrations/0002_seed_admin.py
    migrations/0005_backfill_employee_numbers.py
    migrations/0007_seed_org_admins.py   # Iris Cortez (RH) + Adrian Heymes (ICS)
    tests_org_admins.py            # roles por departamento + notificación
    tests_server_lifecycle.py      # apagado automático (sin esperar 12h reales)
  expenses/
    models.py                  # ExpenseReport, TravelDocument, ExpenseReportAuditLog, validate_trip_span
    pdf_analysis.py             # extracción de monto/tipo (prioriza pág. 1-2) y límite de 4 páginas
    services.py                  # build_travel_document, compartido por subida individual y en lote
    views.py                    # CBVs (ListView/CreateView/DetailView/View + mixins) + preview AJAX
    admin.py                    # panel de aprobación, cláusula CEO, auditoría, alcance por departamento
    excel.py
    tests/                      # test_models, test_excel, test_views, test_pdf_analysis, helpers.py
  templates/
    base.html                    # layout del portal del empleado (en inglés)
    admin/base_site.html          # branding "MHP by Porsche" del panel admin
    admin/index.html               # banner de reportes pendientes por revisar
    admin/login.html                # login admin con formato empresarial
  static/css/
    site.css
    brand.css                     # marca + hover animations compartidas por ambas interfaces
  media/uploads/                # archivos subidos (no versionado, nunca se eliminan — ver módulo 10)
  requirements.txt
```

## Tests

```bash
cd lab2
python manage.py test
```

84 tests: reglas de transición de `ExpenseReport` (incluye deadline y
cláusula CEO), validación de rango de fechas del viaje (`validate_trip_span`),
límite de páginas de PDF y priorización de las primeras 2 páginas, política
de $60/día, análisis de PDF (monto y tipo detectados, y el endpoint de
preview en vivo), creación de reportes con adjuntos múltiples, número de
empleado (generación y unicidad), generación del Excel, signup/aislamiento
entre empleados, subida y envío de documentos, auditoría de reportes,
trazabilidad de logins (exitosos y fallidos), roles de administrador por
departamento (Iris Cortez/RH ve todo, Adrian Heymes solo ICS, sin fugas por
URL directa), el banner de notificación de pendientes, la lógica de apagado
automático del servidor a las 12h, y el flujo de aprobación/rechazo a
través del Django Admin.
