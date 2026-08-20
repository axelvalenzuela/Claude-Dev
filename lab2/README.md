# Laboratorio 2 — Travel Expense Reports

Aplicación web para que cada empleado suba sus documentos de viaje (vuelos,
hoteles, taxis, comidas...), arme un reporte de gastos y lo envíe a revisión.
Un único usuario administrador (actuando bajo la autoridad delegada del CEO,
**Steffan Widmer**) aprueba o rechaza los reportes; el empleado ve el
resultado en su propio portal. Cualquiera de los dos roles puede descargar el
reporte en Excel.

> La interfaz de la aplicación está **en inglés** (plataforma "enterprise"
> orientada a un equipo internacional); esta documentación queda en español
> para el equipo que la mantiene.
>
> Se evaluó inicialmente hacerlo en .NET/C#, pero por restricciones de
> permisos en el equipo de desarrollo se implementó en **Python + Django**.

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
- Test framework de Django (basado en `unittest`): **49 tests**.

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

### Cuenta de administrador (sembrada automáticamente)

- **Correo**: `axel.valenzuela@uabc.edu.mx`
- **Password**: `Admin#2026Local`

> Contraseña de desarrollo local únicamente. Cámbiala editando `.env` (o
> definiendo las variables `ADMIN_SEED_*` antes del primer `migrate`) si vas
> a correr esto fuera de tu máquina.

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

### 5. Cláusula de aprobación del CEO — Steffan Widmer
- `ExpenseReport.approve(reviewer, note, ceo_clause_ack)` **exige**
  `ceo_clause_ack=True` para aprobar; si no se confirma, lanza error.
- Al aprobar, se graba `ceo_authorized=True` y
  `approval_clause = "Approved under authority delegated by Steffan Widmer, CEO."`,
  visible para el empleado y en el Excel.
- En el admin, esto se ve como un **checkbox obligatorio** ("I confirm this
  approval is issued under the authority of Steffan Widmer (CEO)") que debe
  marcarse para poder guardar una aprobación — rechazar no lo requiere, pero
  sí exige una nota con el motivo.

### 6. Panel de administrador — Django Admin (`expenses/admin.py`)
- Accesible solo para la cuenta sembrada (`is_staff=True`); cualquier
  empleado normal es rechazado por el framework mismo.
- **`ExpenseReportAdmin`**: solo reportes ya enviados (los borradores son
  privados del empleado), **ordenados por fecha de envío**
  (`ordering = ["-submitted_at"]`, más reciente primero). Columnas de lista
  incluyen indicador de política ($60/día) y de fecha límite.
- Vista de detalle: desglose diario de gastos con el límite de $60/día
  resaltado, documentos inline (con los campos detectados por el análisis
  de PDF), y el historial de auditoría del reporte inline.
- Aprobar/rechazar reusa las mismas reglas de negocio del modelo
  (`ExpenseReport.approve()`/`reject()`), no las reimplementa.

### 7. Auditoría e histórico de reportes (`ExpenseReportAuditLog`)
- Registro inmutable (solo lectura en el admin) de cada evento del ciclo de
  vida de un reporte: creado, documento subido, documento eliminado,
  enviado, aprobado, rechazado — con quién (`actor`) y cuándo.
- Se escribe desde las vistas del empleado y desde el admin
  (`ExpenseReportAdmin.save_model`). Es el histórico por usuario que
  pediste, más allá del último estado guardado en `ExpenseReport`.
- Ver [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) para el diagrama de
  relaciones completo y el porqué de este diseño.

### 8. Generación de Excel (`expenses/excel.py`)
- Encabezado con empleado/departamento/estado, la cláusula de aprobación del
  CEO si el reporte fue aprobado, la tabla de documentos, y el **desglose
  diario contra la política de $60/día** con las filas fuera de límite
  resaltadas.

### 9. Documentos y almacenamiento (`expenses/models.py`)
- `TravelDocument.file` valida extensión (`.pdf`, `.jpg`, `.jpeg`, `.png`) y
  tamaño máximo (10 MB).
- Nombre físico único (`uuid4`) bajo `media/uploads/{user_id}/{report_id}/`;
  se conserva el nombre original (`original_filename`) para mostrarlo y
  descargarlo.

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

## Estructura

```
lab2/
  manage.py
  .env.example              # variables de entorno documentadas (copiar a .env)
  docs/DATA_MODEL.md          # diagrama ER y trazabilidad
  config/                    # settings (django-environ), urls, wsgi/asgi
  accounts/
    models.py                 # User, LoginEvent
    signals.py                 # graba LoginEvent en cada intento de login
    views.py                   # SignUpView (CBV)
    migrations/0002_seed_admin.py
  expenses/
    models.py                  # ExpenseReport, TravelDocument, ExpenseReportAuditLog
    pdf_analysis.py             # extracción de monto/tipo desde el PDF
    views.py                    # CBVs (ListView/CreateView/DetailView/View + mixins)
    admin.py                    # panel de aprobación, cláusula CEO, auditoría
    excel.py
    tests/                      # test_models, test_excel, test_views, test_pdf_analysis
  templates/base.html           # layout compartido (Bootstrap 5 vía CDN, en inglés)
  static/css/site.css
  media/uploads/                # archivos subidos (no versionado)
  requirements.txt
```

## Tests

```bash
cd lab2
python manage.py test
```

49 tests: reglas de transición de `ExpenseReport` (incluye deadline y
cláusula CEO), política de $60/día, análisis de PDF (monto y tipo
detectados, y el endpoint de preview en vivo), creación de reportes con
adjuntos múltiples, generación del Excel, signup/aislamiento entre empleados,
subida y envío de documentos, auditoría de reportes, trazabilidad de logins
(exitosos y fallidos), y el flujo de aprobación/rechazo a través del Django
Admin.
