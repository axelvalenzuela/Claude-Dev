# Laboratorio 2 — MHP by Porsche · Travel Expense Reports

Aplicación web para que cada empleado suba sus documentos de viaje (vuelos,
hoteles, taxis, comidas...), arme un reporte de gastos y lo envíe a revisión.
El reporte se aprueba (o rechaza, con nota) por el admin del
**departamento** del empleado, o por el admin general de **RH**; el
empleado ve el resultado como notificación en el portal, con la nota si
fue rechazado. Al enviar el reporte se generan un **Excel** y un **Word**
editable con toda la información capturada, y los archivos originales se
eliminan del servidor. Toda aprobación final queda sujeta a la cláusula de
autoridad delegada del CEO, **Steffan Widmer**. Incluye protección local
contra fuerza bruta (bloqueo tras 3 intentos fallidos + reset de
contraseña).

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
- Test framework de Django (basado en `unittest`): **114 tests**.

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

### 2. Portal del empleado (`expenses/views/` — vistas basadas en clases)
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
- **Front-end**: Bootstrap 5 vendorizado localmente (`static/vendor/bootstrap/`,
  no CDN) — necesario para que la app funcione sin salida a internet en un
  servidor de intranet, y de paso elimina un punto único de falla. El menú
  ahora tiene un toggler funcional en pantallas angostas (antes no colapsaba,
  solo se desbordaba) y resalta el link de la página activa (**My reports**
  / **History**).

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

### 8. Panel de administrador — Django Admin (`expenses/admin/`)
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
- **Badge "signed in as ..."**: hasta ahora la única forma de notar la
  diferencia entre un admin de RH y uno de departamento era indirecta (qué
  reportes le aparecen en la cola). Se agregó un badge junto al logo, visible
  en **todas** las páginas del admin (no solo el dashboard), que dice
  explícitamente "HR administrator — all departments" o "ICS department
  administrator" (`accounts/context_processors.py:admin_scope_badge`,
  `templates/admin/base_site.html`).

### 10. Excel + Word al aprobar, y retención de archivos — decisión de buena práctica

Esto cambió de decisión sobre la marcha, dos veces (documentado aquí para
que quede claro el porqué): originalmente los archivos originales nunca se
borraban. Luego se cambió a generar **Excel + Word** y borrar los
originales **al enviar** el reporte. La versión actual mueve ese punto de
corte a **cuando el admin aprueba**, no al enviar — mientras un reporte
sigue en revisión (`submitted`), el empleado o el admin todavía pueden
necesitar ver los archivos originales antes de decidir, así que se
conservan hasta entonces:

- Al aprobar un reporte desde el admin (`ExpenseReportAdmin.save_model`,
  que llama a `ExpenseReport.approve()` y luego a
  `expenses/services.py:finalize_approval()`), **dentro de la misma
  transacción** (Django admin ya envuelve todo el POST del changeform en
  una):
  1. Genera el `.xlsx` (`expenses/excel.py`) y el `.docx`
     (`expenses/word_export.py`) — en este punto el reporte ya está
     aprobado, así que el archivo incluye quién revisó, la nota y la
     cláusula del CEO — y los guarda permanentemente en
     `ExpenseReport.excel_snapshot` / `word_snapshot`, **nombrados con la
     convención de RH**: nombre del empleado, fecha de envío, número de
     empleado y el sufijo `APROBADO` (`expenses/naming.py:
     export_basename()`) — p. ej. `Ana_Lopez_2026-08-15_1234567_APROBADO.xlsx`.
  2. Solo si ambos se guardaron bien, borra el archivo físico de cada
     `TravelDocument` del reporte (`document.file.delete()`) — la fila en
     sí (tipo, monto, fecha, flags de la política) **se conserva**, así que
     el desglose de $60/día, el historial y la auditoría siguen
     funcionando exactamente igual sin el archivo original.
  3. Si algo falla generando los exports, **nada se borra** — toda la
     aprobación se revierte (transacción atómica) y el reporte se queda en
     `submitted`.
- **Un reporte rechazado no se toca**: no existe flujo de reenvío, así que
  sus archivos originales se conservan indefinidamente junto con el motivo
  del rechazo — solo la aprobación dispara el borrado.
- El **Word** (`.docx`, editable) incluye lo mismo que el Excel (datos del
  empleado, departamento, supervisor, fechas del viaje, tabla de gastos
  ordenada **alfabéticamente por tipo**, desglose de $60/día) más una
  sección de **"Receipt captures"**: una miniatura incrustada de cada
  recibo que sea foto (JPG/PNG) — se embebe *antes* de borrar el original,
  así que es el respaldo visual permanente de esas fotos. Los PDF solo se
  listan por nombre (renderizar una página de PDF a imagen necesitaría una
  dependencia de sistema tipo poppler, no se agregó solo para esto).
- Mientras el reporte está en `draft` o `submitted` (pendiente de
  revisión), los links de descarga de **Excel y Word**
  (`ExportExcelView`/`ExportWordView` para el empleado; el campo
  `exports_display` en el admin) generan una vista previa al vuelo, sin
  guardarla, ya con el mismo nombre base (empleado, fecha, número de
  empleado, sin el sufijo `APROBADO` todavía). Una vez aprobado, esos
  mismos links sirven el archivo permanente guardado en el paso anterior.
  La fila de cada documento indica "(archived)" en vez de un link roto una
  vez que el original ya no está.
- Por qué no un "archivo aparte" solo para el admin: el admin **ya** ve
  todo esto entrando al reporte del usuario en `/admin/` (Excel/Word +
  documentos con su estado), que es justo el flujo pedido ("simplemente
  tiene que entrar a gestionar el reporte de ese usuario que ya envió") —
  un archivo aparte solo hubiera duplicado lo mismo dos veces.

### 11. Ordenado alfabético (portal + archivos generados)
- **Dentro de Excel/Word**: la tabla de gastos de un reporte se ordena por
  `type` (Flight/Hotel/Meal/Taxi/Other) y luego por fecha, no por fecha de
  captura — agrupa por categoría, que es lo que se pidió como "orden
  alfabético dentro de los archivos".
- **En el portal**: la vista **History** (empleado) y **Approved reports
  (history)** (admin) — ver puntos 12 y 13 — están ordenadas
  alfabéticamente por título del reporte, porque son vistas de "buscar algo
  que ya pasó", no de "qué necesito hacer hoy". Las colas de trabajo activo
  (**My reports** del empleado, la bandeja de aprobación del admin) se
  quedan ordenadas por fecha — para triage, lo más reciente primero es más
  útil que el orden alfabético.

### 12. Historial del empleado (`ReportHistoryView`, `/reports/history/`)
- Todo lo que el empleado ha enviado alguna vez (`submitted`/`approved`/
  `rejected` — nunca borradores, que no se le han mandado a nadie),
  ordenado alfabéticamente por título.
- Incluye la **nota del administrador** en la misma fila — si un reporte
  fue rechazado alguna vez, ese motivo queda visible ahí permanentemente,
  no solo en el detalle del reporte.

### 13. Historial de aprobados del admin (`ApprovedExpenseReport`, proxy model)
- Aparece como su propia sección en Django Admin ("Approved reports
  (history)"), no solo como un filtro sobre la bandeja de trabajo —
  modelo *proxy* de `ExpenseReport` (misma tabla, sin migraciones nuevas de
  esquema) registrado por separado en `expenses/admin/approved_history.py`.
- Ordenado alfabéticamente por título; de **solo lectura** (no se puede
  agregar/editar/borrar desde ahí — aprobar/rechazar sigue siendo solo
  desde la bandeja de trabajo normal); respeta el mismo alcance por
  departamento que el resto (Adrian Heymes solo ve aprobados de ICS, Iris
  Cortez ve todos).

### 14. Notificaciones de aprobación/rechazo (lado del empleado)
- Mientras navega el portal (cualquier página, no solo el detalle del
  reporte), el empleado ve un banner si alguno de sus reportes fue
  aprobado o rechazado en los últimos 7 días
  (`accounts/context_processors.py:recent_review_notification`), con la
  **nota del administrador** incluida ahí mismo si la hay — no solo un
  "fue rechazado" sin explicación.
- Pasados esos 7 días el banner deja de mostrarse (para no acumular avisos
  viejos), pero el reporte y su nota **siguen disponibles para siempre** en
  History (punto 12) y en el propio detalle del reporte.

### 15. Gráfica circular de aprobación/rechazo (lado del admin)
- En el dashboard de `/admin/`, un donut chart (CSS puro,
  `conic-gradient` — sin librería de gráficas ni JS) muestra qué proporción
  de lo que ese admin ha revisado fue aprobado vs. rechazado
  (`accounts/context_processors.py:approval_chart`).
- Respeta el mismo alcance por departamento que la bandeja y la
  notificación: Adrian Heymes ve su propio approved/rejected de ICS; Iris
  Cortez ve el total de la empresa.

### 16. Seguridad local: bloqueo de cuenta tras 3 intentos fallidos
- `accounts/security.py:is_account_locked()` reusa el propio `LoginEvent`
  (ver punto 1) en vez de agregar un campo de estado aparte: si los
  últimos **3** intentos de login para un correo son todos fallidos, la
  cuenta queda bloqueada — **incluso si el siguiente intento trae la
  contraseña correcta**, se rechaza igual, con el mensaje "Too many failed
  login attempts... Reset your password to regain access."
- Aplica **tanto al login del empleado como al del admin**
  (`accounts/forms.py:LockoutCheckMixin`, usado por `LoginForm` y por
  `AdminLoginForm` — este último conectado a Django Admin vía
  `admin.site.login_form` en `accounts/apps.py`).
- **Reset de contraseña real**: se agregaron las vistas de Django
  (`password_reset`, `password_reset_confirm`, etc.) con plantillas de
  marca; en local, `EMAIL_BACKEND` está configurado a la consola (el
  correo con el link de reset se imprime en la terminal, no requiere SMTP).
  El link de "Forgotten your password?" es el mismo en ambos logins
  (empleado y admin) — una sola cuenta, un solo flujo de reset.
- Completar el reset **desbloquea la cuenta de inmediato**: `accounts/
  views.py:PasswordResetConfirmView` registra un `LoginEvent(success=True)`
  sintético en cuanto se guarda la nueva contraseña, que es justo lo que
  `is_account_locked()` revisa — sin este paso, resetear la contraseña por
  sí solo no habría cambiado el historial de intentos.
- Endurecido adicional en `settings.py` (aplicable en local):
  `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY`,
  `X_FRAME_OPTIONS = "DENY"`, `SECURE_CONTENT_TYPE_NOSNIFF` — además de lo
  que Django ya trae por default (CSRF en todos los POST, passwords
  hasheados, validadores de contraseña).

### 17. Generación de Excel (`expenses/excel.py`)
- Encabezado con empleado, **número de empleado**, departamento, supervisor,
  **fechas del viaje**, estado y fecha de creación; la cláusula de
  aprobación del CEO si el reporte fue aprobado; la tabla de documentos
  (ordenada por tipo, ver punto 11); y el **desglose diario contra la
  política de $60/día** con las filas fuera de límite resaltadas. Formato
  pensado para verse como un reporte corporativo real, no una tabla suelta.
- Ver punto 10 para cuándo se genera y guarda permanentemente vs. cuándo se
  genera al vuelo.

### 18. Documentos y almacenamiento (`expenses/models.py`)
- `TravelDocument.file` valida extensión (`.pdf`, `.jpg`, `.jpeg`, `.png`),
  tamaño máximo (10 MB) y número de páginas (PDFs, máximo 4).
- Nombre físico único (`uuid4`) bajo `media/uploads/{user_id}/{report_id}/`;
  se conserva el nombre original (`original_filename`) para mostrarlo,
  aun después de que el archivo se elimine al enviar (ver punto 10).

### 19. Auditoría e histórico de reportes (`ExpenseReportAuditLog`)
- Registro inmutable (solo lectura en el admin) de cada evento del ciclo de
  vida de un reporte: creado, documento subido, documento eliminado
  (incluye el borrado en lote al enviar, ver punto 10), enviado, aprobado,
  rechazado — con quién (`actor`) y cuándo.
- Se escribe desde las vistas del empleado y desde el admin
  (`ExpenseReportAdmin.save_model`). Es el histórico por usuario que
  pediste, más allá del último estado guardado en `ExpenseReport`.
- Ver [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) para el diagrama de
  relaciones completo y el porqué de este diseño.

### 20. Número de empleado (`accounts/models.py`)
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

`expenses/services.py:finalize_approval()` corre justo después de un
`approve()` exitoso (misma transacción): genera Excel + Word con el nombre
de RH y solo entonces borra los archivos originales — ver módulo 10.

## Organización del código y convenciones

Revisado y refactorizado para que el tamaño de cada archivo se mantenga
manejable y cada uno tenga una sola responsabilidad clara — la regla que se
siguió: **en cuanto un `views.py`/`admin.py`/archivo de tests empieza a
mezclar varias responsabilidades distintas (no solo crecer en líneas), se
divide por responsabilidad, nunca por tamaño arbitrario.**

- **`views.py` → paquete `views/`** (`expenses/views/`): en vez de un solo
  archivo con las 11 vistas del portal del empleado, se separó en
  `reports.py` (el reporte en sí: lista, historial, crear, detalle,
  enviar), `documents.py` (un documento suelto: subir/borrar/descargar/
  preview) y `exports.py` (descargar Excel/Word), con `mixins.py` para lo
  compartido (`OwnedReportMixin`). El `__init__.py` re-exporta todo, así
  que `expenses/urls.py` sigue haciendo `from . import views` /
  `views.ReportListView` sin enterarse de en qué archivo vive cada clase —
  el refactor no cambió ninguna URL ni comportamiento.
- **`admin.py` → paquete `admin/`** (`expenses/admin/`): mismo criterio —
  `reports.py` (la bandeja de aprobación), `approved_history.py` (el
  historial de aprobados), `audit_log.py` (la auditoría), más `forms.py`,
  `inlines.py` y `mixins.py` (`ExpenseReportDisplayMixin`, compartido entre
  `reports.py` y `approved_history.py` para no duplicar las columnas
  `employee`/`total_amount_display`/etc.). El `__init__.py` solo importa
  los submódulos — cada uno se registra a sí mismo con `@admin.register`,
  que es como Django ya esperaba que funcionara.
- **Política de negocio separada del esquema**: `expenses/models.py` ya
  solo define las tablas (`ExpenseReport`, `TravelDocument`, ...) y sus
  métodos de dominio; los límites y reglas transversales
  (`DAILY_LIMIT_USD`, `SUBMISSION_WINDOW_DAYS`, `MAX_TRIP_SPAN_DAYS`,
  `CEO_NAME`, `validate_trip_span()`) viven en `expenses/policies.py`, y el
  validador genérico de tamaño de archivo en `expenses/validators.py`
  (el de páginas de PDF se queda en `pdf_analysis.py`, porque solo ese
  módulo necesita `pypdf`). Cambiar el límite diario de $60 nunca implica
  tocar el archivo que define las tablas, y viceversa.
- **`tests/` como paquete, no archivos sueltos**: `accounts/` tenía
  `tests.py` + tres archivos `tests_algo.py` sueltos — se unificó en
  `accounts/tests/` (igual que `expenses/tests/` ya estaba), con un
  archivo por concepto probado (`test_signup.py`, `test_security.py`,
  `test_approval_chart.py`, ...) en vez de por "cuándo se escribió". El
  antiguo `expenses/tests/test_views.py` (558 líneas, 4 clases que en
  realidad probaban cosas distintas) se dividió igual: `test_report_creation.py`,
  `test_report_submission.py`, `test_report_access.py`, `test_exports.py`,
  `test_document_preview.py`, `test_report_history.py`,
  `test_admin_approval.py` — cada uno nombrado por lo que prueba, no por
  la vista que lo genera, así se encuentra sin tener que adivinar.
- **Docstrings de módulo**: todo archivo no trivial explica, en 1-3
  líneas al inicio, *qué* vive ahí y *por qué* está separado así — no qué
  hace cada línea (para eso ya están los nombres), sino la decisión de
  diseño detrás del archivo cuando no es obvia solo con el nombre.

### Patrón Decorator

Ya estaba presente de forma implícita en todo lo que provee Django
(`@admin.register`, `@receiver`, `@property`, `LoginRequiredMixin`); se
revisó el código propio de la app y se aplicó explícitamente donde había
lógica transversal duplicada, en vez de solo por usarlo:

- **`expenses/admin/decorators.py:staff_permission`** — `ExpenseReportAdmin`
  tenía tres métodos (`has_module_permission`, `has_view_permission`,
  `has_change_permission`) con exactamente el mismo cuerpo de dos líneas.
  Ahora es un solo decorador aplicado a los tres.
- **`expenses/views/decorators.py:draft_only`** — `UploadDocumentView` y
  `DeleteDocumentView` repetían el mismo guard ("solo mientras el reporte
  sigue en `draft`") con distinto mensaje. El decorador lo centraliza y de
  paso les pasa el reporte ya cargado (`report=`), sin que cada vista tenga
  que volver a pedirlo.

### Interfaz enterprise (Separated Interface / Strategy)

`expenses/exporters.py` define una interfaz formal (`ReportExporter`, una
`ABC` con `build()` abstracto) para los dos formatos exportables — antes,
`services.py:finalize_approval` y `views/exports.py` repetían, una vez por
formato, la misma ceremonia de "generar a `BytesIO`, leer los bytes,
guardar/servir" (4 bloques casi idénticos entre los dos archivos), y el
content-type de Word estaba además hardcodeado por segunda vez en
`views/exports.py`. Ahora ambos puntos de uso pasan por `excel_exporter` /
`word_exporter`; agregar un tercer formato en el futuro (p. ej. PDF) es
agregar una clase en `exporters.py`, no tocar `services.py` ni las vistas.

Esto formaliza un patrón que la app ya seguía en espíritu — el **Service
Layer** de Fowler (`expenses/services.py`, lógica de negocio fuera de
vistas/admin) y los **Policy objects** (`expenses/policies.py`,
`validators.py`) ya son ejemplos de "programar contra una interfaz/
separación de responsabilidades", típicos de arquitectura enterprise —
`exporters.py` es la primera vez que esa interfaz se declara explícitamente
con una clase abstracta en vez de solo por convención de nombres.

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para cómo está armado el
panel de admin en concreto: los tabs del Dashboard, los tabs de la página
de revisión de un reporte (cómo funciona la clasificación de fieldsets por
JS), y los context processors detrás de cada uno.

## Estructura

```
lab2/
  manage.py
  Dockerfile                    # imagen para desplegar en servidor de intranet — ver docs/DEPLOYMENT.md
  docker-compose.yml             # levanta la imagen con datos persistentes en un volumen
  .dockerignore
  .env.example                 # variables de entorno documentadas (copiar a .env)
  docs/DATA_MODEL.md            # diagrama ER y trazabilidad
  docs/DEPLOYMENT.md             # contenedores, HTTPS, base de datos, CI — despliegue en intranet
  docs/ARCHITECTURE.md           # cómo está armado el panel de admin: tabs, context processors, patrones
  config/                       # settings (django-environ, AUTO_SHUTDOWN_HOURS, branding, email/lockout), urls, wsgi/asgi
  accounts/
    models.py                    # User (+ employee_number, supervised_department), LoginEvent
    signals.py                    # graba LoginEvent en cada intento de login
    security.py                    # is_account_locked() — bloqueo tras 3 fallos
    context_processors.py          # notificaciones (pendientes, aprobado/rechazado) + donut chart
    server_lifecycle.py            # apagado automático del runserver a las 12h
    forms.py                       # LoginForm/AdminLoginForm/reset — LockoutCheckMixin
    views.py                       # SignUpView, PasswordResetConfirmView (CBVs)
    admin.py                       # UserAdmin, LoginEventAdmin (solo lectura)
    migrations/0002_seed_admin.py
    migrations/0005_backfill_employee_numbers.py
    migrations/0007_seed_org_admins.py   # Iris Cortez (RH) + Adrian Heymes (ICS)
    tests/                          # un archivo por concepto: signup, security, org_admin_seed,
                                     # department_scoping, notifications, approval_chart, server_lifecycle...
  expenses/
    models.py                  # ExpenseReport (+ excel/word_snapshot), TravelDocument, AuditLog
    policies.py                 # DAILY_LIMIT_USD, SUBMISSION_WINDOW_DAYS, MAX_TRIP_SPAN_DAYS, CEO_NAME, validate_trip_span
    validators.py                # validate_file_size (genérico; el de páginas de PDF vive en pdf_analysis.py)
    pdf_analysis.py             # extracción de monto/tipo (prioriza pág. 1-2) y límite de 4 páginas
    services.py                  # build_travel_document + finalize_approval (exports y borrado de originales, al aprobar)
    exporters.py                  # ReportExporter (interfaz) + ExcelExporter/WordExporter — ver "Interfaz enterprise"
    naming.py                     # export_basename() — convención de nombre de RH (empleado, fecha, número, APROBADO)
    word_export.py                # genera el .docx (con miniaturas de fotos) al aprobar
    views/                       # reports.py, documents.py, exports.py, mixins.py, decorators.py (draft_only) — ver arriba
    admin/                        # reports.py, approved_history.py, audit_log.py, forms.py, inlines.py, mixins.py, decorators.py (staff_permission)
    excel.py
    tests/                      # un archivo por vista/servicio probado — ver arriba
  templates/
    base.html                    # layout del portal del empleado (en inglés) + banner de notificaciones
    admin/base_site.html          # branding "MHP by Porsche" del panel admin
    admin/index.html               # banner de pendientes + donut chart de aprobación
    admin/login.html                # login admin con formato empresarial
    registration/                   # password_reset_*.html con la marca de la app
  static/css/
    site.css
    brand.css                     # marca, hover animations, donut chart y badge de rol admin, compartidos por ambas interfaces
  static/vendor/bootstrap/       # Bootstrap 5 vendorizado (no CDN) — necesario para funcionar sin internet
  media/uploads/                # archivos subidos (no versionado; se borran al enviar — ver módulo 10)
  staticfiles/                   # salida de `collectstatic` (no versionado; solo se usa en producción)
  requirements.txt
```

## Tests

```bash
cd lab2
python manage.py test
```

118 tests: reglas de transición de `ExpenseReport` (incluye deadline y
cláusula CEO), validación de rango de fechas del viaje (`validate_trip_span`),
límite de páginas de PDF y priorización de las primeras 2 páginas, política
de $60/día, análisis de PDF (monto y tipo detectados, y el endpoint de
preview en vivo), creación de reportes con adjuntos múltiples, número de
empleado (generación y unicidad), generación del Excel y del Word (incluida
la miniatura embebida de fotos), `finalize_approval` (exports guardados con
el nombre de RH + borrado de originales + auditoría, disparado al aprobar
—no al enviar— y no al rechazar), signup/aislamiento entre empleados,
subida y envío de documentos, historial alfabético del empleado (con nota
de rechazo) y del admin (proxy de aprobados), auditoría de reportes,
trazabilidad de logins (exitosos y fallidos), roles de administrador por
departamento (Iris Cortez/RH ve todo, Adrian Heymes solo ICS, sin fugas por
URL directa), las notificaciones de pendientes y de aprobado/rechazado, el
donut chart de aprobación, el bloqueo de cuenta tras 3 intentos fallidos
(empleado y admin) más el flujo de reset que lo levanta, la lógica de
apagado automático del servidor a las 12h, y el flujo de aprobación/rechazo
a través del Django Admin.

Lo que estos tests **no** cubren (y por qué): el render visual del front-end
(nav responsive, estado "active" de los links, el badge de rol admin) — son
cambios de plantilla/CSS, no de lógica de negocio, así que se verificaron
manualmente (servidor local + smoke test) en vez de con aserciones
automatizadas sobre HTML.

## Despliegue en servidor de intranet

La app se documenta y prueba como servidor de desarrollo local. Para
correrla en un servidor de intranet de la empresa se agregó soporte para
contenedores (`Dockerfile`, `docker-compose.yml`) y un pipeline de CI de
ejemplo (`.github/workflows/lab2-ci.yml`) — ver
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) para el cómo y el porqué
(incluye por qué se eligió contenedores sobre una instalación directa en el
servidor).
