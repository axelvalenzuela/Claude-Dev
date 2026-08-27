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
- **Pillow** para el chequeo de calidad (no OCR) de recibos en foto — ver
  [`docs/adr/0010-image-quality-check-not-ocr.md`](docs/adr/0010-image-quality-check-not-ocr.md).
- Test framework de Django (basado en `unittest`): **212 tests**.

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

Cinco cuentas con acceso a `/admin/`, cada una representando un rol
distinto del organigrama:

| Rol | Correo | Password | Alcance |
|---|---|---|---|
| Admin general (RH) | `iris.cortez@mhp.com` | `Iris#2026Local` | **Iris Cortez** — ve y aprueba reportes de **todos** los departamentos (`is_superuser`). Es la aprobadora final por defecto. |
| Admin general (RH) | `karen.plascencia@mhp.com` | *(ver nota abajo — password aleatorio, solo en tu `.env` local)* | **Karen Plascencia** — mismo alcance que Iris Cortez (`is_superuser`), segunda admin general. |
| Admin general (CEO) | `steffan.widmer@mhp.com` | `Steffan#2026Local` | **Steffan Widmer** — el CEO cuya autoridad delegada ya se menciona en la cláusula de aprobación (`expenses/policies.py:CEO_NAME`); mismo alcance que Iris/Karen (`is_superuser`). |
| Admin de departamento (ICS) | `adrian.heymes@mhp.com` | `Adrian#2026Local` | **Adrian Heymes** — ve y aprueba **solo** reportes de empleados con `department="ICS"`. |
| Bootstrap (dev) | `axel.valenzuela@uabc.edu.mx` | `Admin#2026Local` | Cuenta genérica de arranque local, configurable vía `ADMIN_SEED_*`; independiente del organigrama. |

**Las cuatro pueden ver y gestionar Users & Groups** (no solo las
`is_superuser`) — Adrian, como cualquier cuenta `is_staff`, también puede
abrir una cuenta y marcarle `is_staff`/`is_superuser`/`supervised_department`
para darle acceso de admin a alguien más. Ver `accounts/admin.py:
StaffManagedAdminMixin`.

Y una cuenta de **empleado regular, sin acceso a `/admin/`**:

| Correo | Password | Departamento |
|---|---|---|
| `axel.valenzuela@mhp.com` | *(ver nota abajo — no committeado)* | ICS |

**`axel.valenzuela@mhp.com` es intencionalmente NO admin** — es la
identidad de dominio MHP para probar el lado del empleado (subir recibos,
enviar un reporte, esperar a que alguno de los admins de arriba lo
apruebe), separada de la cuenta bootstrap (`@uabc.edu.mx`) para no tener
que cerrar sesión de admin cada vez que se quiere probar el flujo de
empleado.

Un empleado de ICS (p. ej. `axel.valenzuela@mhp.com`, con
`department="ICS"`) solo aparece en la bandeja de aprobación de **Adrian
Heymes**; cualquiera de las admin generales (**Iris Cortez**, **Karen
Plascencia**, **Steffan Widmer**) ve ese mismo reporte y el de cualquier
otro departamento. Ver la sección de "Roles de administrador" más abajo.

> Contraseñas de desarrollo local únicamente. Cámbialas editando `.env` (o
> las variables `HR_ADMIN_*` / `ICS_ADMIN_*` / `ADMIN_SEED_*` antes del
> primer `migrate`) si vas a correr esto fuera de tu máquina.
>
> **`axel.valenzuela@mhp.com` y `karen.plascencia@mhp.com` son la
> excepción**: a diferencia de las demás cuentas de esta tabla, sus
> passwords reales **no** están hardcodeados como default en la migración
> ni en este README — viven solo en tu `.env` local (gitignored,
> `AXEL_MHP_EMPLOYEE_PASSWORD` / `KAREN_ADMIN_PASSWORD`), precisamente
> porque uno de los dos es un password personal real que no debe quedar en
> el historial de git. El default committeado en la migración
> (`ChangeMe#2026Local`) solo aplica si tu `.env` no define esa variable.
>
> **Login por número de empleado**: cualquier cuenta (admin o empleado)
> también puede iniciar sesión escribiendo su **número de empleado** en
> vez del correo, tanto en `/accounts/login/` como en `/admin/login/` —
> ver "Login con email o número de empleado" más abajo.

### Login con email o número de empleado

El campo de login (empleado y admin, mismo formulario base) acepta **el
correo o el número de empleado** — es común no acordarse de cuál de los
dos usar, y ambos ya identifican una sola cuenta de forma única, así que
no tenía sentido forzar un solo campo.

- `accounts/backends.py:EmployeeNumberOrEmailBackend` reemplaza el
  `ModelBackend` por default de Django en `AUTHENTICATION_BACKENDS`
  (`config/settings.py`): primero intenta resolver lo que se escribió como
  email (comportamiento normal, sin cambios), y si no encuentra nada,
  reintenta como número de empleado, antes de verificar la contraseña.
- `accounts/models.py:find_user_by_login_identifier()` es la única función
  que sabe que ambos identificadores son válidos — la usan tanto el
  backend de autenticación como el chequeo de bloqueo por intentos
  fallidos (`LockoutCheckMixin.clean()`) y la bitácora de intentos
  fallidos (`accounts/signals.py:record_failed_login`), para que los tres
  se pongan de acuerdo en qué cuenta es "la misma cuenta" sin importar cuál
  identificador se haya escrito en un intento en particular.
- Esto importa para el bloqueo de cuenta (3 intentos fallidos seguidos, ver
  más abajo): sin esta normalización, fallar 2 veces con el correo y una
  vez con el número de empleado se habría repartido en dos contadores
  separados de "menos de 3", nunca activando el bloqueo — con la
  normalización, las tres fallas cuentan para la misma cuenta sin importar
  qué se haya escrito cada vez.
- Un login **exitoso** siempre queda registrado en `LoginEvent` con el
  correo real de la cuenta (sin cambios en esa parte) — solo el registro de
  intentos **fallidos** necesitaba la normalización, porque antes se
  guardaba literalmente lo que la persona escribió.

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
- **Log in / Log out** del portal vía **JWT** (cookies `HttpOnly` con
  access token de corta duración + refresh token, `accounts/jwt_auth.py`)
  en vez del sistema de sesiones de Django — ver
  `docs/adr/0011-jwt-web-authentication.md`. El Admin de Django
  (`/admin/`) sigue con su propio login de sesión, sin cambios: no hay
  forma soportada de correr `django.contrib.admin` sobre un token sin
  estado.
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
- **Buscador en "My reports"** (`report_list.html`): filtro por título o
  estatus, del lado del cliente (sin ir al servidor), el mismo patrón que
  ya usaba la pestaña Employees del Dashboard del admin. Solo aparece
  pasando de 5 reportes — con menos, desplazarse ya es instantáneo.
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
  documentos mientras el reporte sigue en `draft`, desde su propia página
  de detalle. Este uploader (arrastrar/soltar, varios archivos a la vez,
  preview en vivo, tabs por archivo) es **el mismo componente** que el de
  crear un reporte nuevo — antes era un formulario de un solo archivo con
  recarga de página completa; ahora comparten exactamente el mismo
  `static/js/document-uploader.js` y la misma plantilla
  `expenses/_document_uploader.html`, para que agregar un recibo a un
  reporte que ya empezaste se sienta igual que empezar uno desde cero
  (ver `docs/adr/0012-shared-frontend-js-not-a-react-rewrite.md`). Cada
  archivo se sigue subiendo con su propia petición al mismo
  `UploadDocumentView` de siempre — el uploader solo cambió cómo se ven y
  arman esas peticiones, no la validación del servidor.
- **Análisis del PDF al subirlo** (`expenses/pdf_analysis.py`): lee el texto
  del PDF y adivina el monto total y el tipo de gasto por palabras clave
  (`boarding pass`→flight, `hotel/check-in`→hotel, `uber/taxi`→taxi,
  `restaurant/dinner`→meal). Si el monto o el tipo detectado no coincide con
  lo que el empleado capturó, se marca `amount_mismatch` / `type_mismatch` y
  se le avisa — así se evitan errores/posibles incumplimientos de política
  desde el origen, no solo al aprobar.
- **También adivina fecha, proveedor y moneda** (mismo módulo): una fecha
  con formato numérico común (`MM/DD/YYYY`, ISO, etc. — nunca una fecha
  futura, señal de un dígito mal leído), la primera línea corta con letras
  de la página 1 como proveedor probable (heurística deliberadamente más
  floja que monto/tipo — sin lista de palabras clave que la ancle, así que
  se omite en vez de adivinar mal), y "MXN"/"peso" vs. "USD"/"dollar" en el
  texto para la moneda. En la página de "New expense report", cada pestaña
  de archivo muestra una nota **arriba** de los campos indicando
  explícitamente qué se detectó de verdad contra qué quedó en su valor por
  default (fecha de hoy, USD) — para que un default nunca se confunda con
  un dato real leído del recibo.
- **Chequeo de calidad para fotos** (`expenses/image_analysis.py`,
  [`docs/adr/0010-image-quality-check-not-ocr.md`](docs/adr/0010-image-quality-check-not-ocr.md)):
  una foto (JPG/PNG) no tiene texto que leer, así que **no** se le hace
  OCR — deliberadamente, ver el ADR para el porqué (Tesseract es una
  dependencia de sistema, no un paquete de pip; una API de OCR en la nube
  tendría costo por llamada e internet obligatorio, el mismo trade-off ya
  rechazado para el chat de ayuda). Lo que sí se revisa con Pillow: si el
  archivo realmente abre como imagen, su resolución, y si se ve borrosa
  (varianza de bordes sobre una copia en escala de grises, calibrada con
  imágenes de prueba sintéticas — ver el comentario de
  `BLUR_VARIANCE_THRESHOLD`). El resultado se muestra igual que el de un
  PDF: una nota arriba de los campos de esa pestaña, dejando claro que
  ningún campo se pre-llenó (solo la fecha/USD por default) y avisando si
  la foto en sí no se ve confiable.
- **Sin límite de archivos**: nada en el código limita cuántos PDFs/fotos
  se pueden adjuntar a un reporte — se pueden ir agregando de uno en uno o
  varios a la vez, en cualquier combinación, y todos se acumulan (ver el
  bug fix de abajo). El único límite real es el tamaño por archivo
  (`MAX_FILE_SIZE_MB` en `validators.py`, 10 MB) y el límite genérico de
  Django de cuántos campos puede traer un POST
  (`DATA_UPLOAD_MAX_NUMBER_FIELDS`, no modificado aquí a propósito — es
  una protección contra agotamiento de memoria, y un viaje real no se
  acerca ni de lejos a los cientos de documentos que haría falta para
  tocarlo).
- **Pistas al pasar el mouse**: cada campo de "New expense report" (título,
  descripción, supervisor, y los de cada documento) tiene un ícono
  `?` junto a la etiqueta — al pasar el mouse (tooltip de Bootstrap)
  explica qué poner ahí, con un ejemplo cuando aplica.
- **Corrección: adjuntar en más de una interacción ya no reemplazaba lo
  anterior** — antes, arrastrar o seleccionar un archivo sustituía por
  completo lo ya adjuntado (comportamiento nativo del input de archivos),
  así que solo "sobrevivía" la última tanda. Ahora una lista propia en
  JavaScript (`selectedFiles`) es la que manda; cada agregar/quitar pasa
  por ahí primero y el input nativo se reconstruye a partir de ella, nunca
  al revés.
- **Supervisor**: cada reporte guarda `supervisor_name` (obligatorio) y
  `supervisor_email` (opcional) — a quién queda dirigido el envío. Visible
  en el detalle, en el admin y en el Excel. En "New expense report" se
  elige de un **combo box** poblado con el organigrama de admins reales
  (`expenses/views/reports.py:_supervisor_choices()` — cualquier cuenta
  `is_staff` activa), no texto libre; el campo de correo junto a él es
  de **solo lectura** (gris) y se autocompleta con el correo real de
  quien se eligió — nunca se escribe a mano, así que no puede
  desincronizarse de a quién en verdad se le va a enviar.
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
- **Conversión de moneda**: `TravelDocument.currency` (USD o MXN, USD por
  default) registra en qué moneda se emitió el recibo — el empleado la
  elige al subir el documento. El límite de $60/día siempre está en
  dólares, así que compararlo contra un monto en pesos sin convertir daría
  falsos positivos (p. ej. $292.98 MXN en 3 viajes de Uber son solo
  ~$17 USD, muy por debajo de $60 — comparar los pesos directamente contra
  $60 los marcaría como violación sin serlo). `TravelDocument.amount_usd`
  hace la conversión con una tasa fija (`USD_MXN_RATE` en
  `expenses/policies.py`, 17 pesos por dólar — es una herramienta interna,
  no un sistema de tesorería con tasa en vivo) y es lo único que se compara
  contra el límite; `amount` original nunca se altera, se conserva tal
  cual se capturó. `ExpenseReport.total_amount` también suma en
  `amount_usd`, no en `amount`, por la misma razón — el total de un reporte
  que mezcla monedas no tiene sentido si no se convierten primero.
- **Formato de tabla igual al Advance & Expense Report real de la empresa**:
  la tabla de gastos (portal del empleado, tab Summary del admin, Excel y
  Word) usa las mismas columnas que esa planilla — Invoice date,
  Description, Vendor legal name, Expensed amount in foreign currency,
  Currency, FX Rate, Backup, y "Amount (USD)" en vez de "Total MXN" (porque
  la política de esta app es en dólares, no en pesos) — con esa última
  columna resaltada en verde igual que en el Excel original.
  `TravelDocument.vendor_name` y `backup_type` (Invoice/No invoice) son
  campos nuevos que el empleado captura al subir cada documento
  (`expenses/forms.py:TravelDocumentForm`); `vendor_name` es obligatorio
  para subidas nuevas pero `blank=True` a nivel de modelo para no romper
  documentos que ya existían antes de este campo. No se agregó "Account
  Number" (el código contable interno) porque no hay forma confiable de
  inferirlo automáticamente sin datos reales de contabilidad.
- **Excepción de vuelos/hoteles**: un día con un documento tipo `FLIGHT` u
  `HOTEL` casi siempre va a superar los $60 por sí solo — eso no es una
  falta a la política, es lo esperado. `daily_totals()` marca esos días con
  `has_flight_or_hotel=True` y **no** los marca como `over_limit` aunque el
  total sea mucho mayor a $60; un día sin vuelo/hotel que de todos modos
  supera los $60 (p. ej. varios taxis o comidas) sí se marca `over_limit`
  normalmente. La distinción se calcula **una sola vez, en este método** —
  ni el Excel, ni el Word, ni el admin, ni el portal del empleado
  reimplementan la regla, todos leen el mismo `over_limit`/
  `has_flight_or_hotel` que ya viene calculado (ver "Centralización de
  políticas" más abajo).
- Cualquier día realmente fuera de política se marca `over_limit=True` —
  rojo para el empleado (detalle del reporte), para el admin (lista +
  detalle, con ⚠) y en el Excel exportado (fila resaltada en rojo). Un día
  con vuelo/hotel se marca en **azul** (informativo, no alerta) con la
  nota "Flight/Hotel" en vez de "Yes"/rojo.
- `ExpenseReport.has_policy_violations` resume si el reporte completo tiene
  algún día *realmente* fuera de política (excluyendo los días de vuelo/
  hotel) — es la señal de "posible falta a las políticas de la empresa"
  que pediste.

**Centralización de políticas**: la regla completa (límite de $60,
conversión de moneda, excepción de vuelo/hotel) vive en un solo lugar —
`ExpenseReport.daily_totals()` (`expenses/models.py`), respaldada por
`DAILY_LIMIT_USD` y `USD_MXN_RATE` en `expenses/policies.py`. Cada vista
(Excel, Word, admin, portal del empleado) solo *muestra* el resultado
(color/texto/el monto ya convertido), nunca vuelve a calcular la regla ni
la conversión — así que cambiar la política (el monto, la tasa de cambio,
o qué tipos quedan exentos) siempre es un cambio en un solo archivo, y
todas las superficies quedan sincronizadas automáticamente.

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
- **Organigrama sembrado** (`accounts/migrations/0007_seed_org_admins.py`,
  `0009_seed_karen_admin.py`, `0010_seed_steffan_widmer.py`): Iris Cortez
  (RH, general), Adrian Heymes (ICS), Karen Plascencia (RH) y Steffan
  Widmer (RH, CEO) — ver la tabla de credenciales más arriba.
  `0008_seed_axel_mhp_employee.py` siembra la identidad MHP de Axel
  Valenzuela como **empleado**, no admin — no forma parte del organigrama.
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
- **Un reporte rechazado no dispara el borrado por aprobación**: no existe
  flujo de reenvío, así que sus archivos originales no se borran al
  rechazar — pero sí quedan sujetos a la **política de retención de 90
  días** igual que cualquier otro documento pendiente (ver más abajo), no
  se conservan indefinidamente.
- El **Word** (`.docx`, editable) incluye lo mismo que el Excel (datos del
  empleado, departamento, supervisor, fechas del viaje, tabla de gastos
  ordenada **alfabéticamente por tipo**), pero sin la tabla aparte de
  desglose diario que sí tiene el Excel: un día que excede los $60/día se
  marca directamente en su propia fila de la tabla de gastos (fecha en
  rojo con ⚠, más una nota corta al final listando esas fechas si aplica)
  — una segunda tabla completa repitiendo las mismas fechas solo saturaría
  al lector. Además incluye una sección de **"Receipt captures"**: una
  captura de **cada recibo**, no
  solo fotos — un PDF también se renderiza a imagen (primera página, vía
  `expenses/receipt_capture.py` con PyMuPDF, que instala como paquete de
  pip normal, sin dependencia de sistema tipo poppler) — ordenadas por
  **fecha del gasto**, no por tipo, para que se lean en el orden en que
  pasó el viaje. Se embeben *antes* de borrar el original, así que es el
  respaldo visual permanente de cada recibo. El mismo render se usa para
  la galería "Receipt captures" del tab Summary del admin, para poder
  verlas sin descargar nada (mientras el original siga en el servidor).
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
- **Retención de 90 días para lo que nunca se aprueba**: la aprobación ya
  borra los originales de inmediato, pero un reporte que se queda
  `submitted` sin que nadie lo revise, o que se rechaza, antes se quedaba
  con sus archivos originales para siempre. Ahora hay un límite:
  `expenses/management/commands/cleanup_old_documents.py` (programado por
  fuera de la app — cron/Task Scheduler, ver `docs/DEPLOYMENT.md`) borra el
  archivo original de cualquier `TravelDocument` que lleve más de
  `FILE_RETENTION_DAYS` (90, `expenses/policies.py`) días subido, sin
  importar el estado del reporte — el reporte y la fila del documento
  **no** se tocan, solo el archivo, igual que hace la aprobación.

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
- El conteo de 3 intentos es **el mismo sin importar si se escribió el
  correo o el número de empleado** en cada intento — ver "Login con email o
  número de empleado" más arriba para por qué eso necesitó normalizar el
  identificador antes de contar, no solo antes de autenticar.
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
- **Logout revoca de verdad**, no solo borra cookies: `JWTLogoutView`
  además pone en lista negra (`accounts/models.py:BlacklistedToken`) el
  refresh token de la sesión, para que no se pueda usar después de
  cerrar sesión para renovar el access token silenciosamente. Programar
  `manage.py cleanup_expired_tokens` (junto con `cleanup_old_documents`,
  ver `docs/DEPLOYMENT.md`) para no acumular filas vencidas.

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
- Descargable directamente desde el panel de un reporte: el botón
  **"Download history"** (arriba del formulario, donde antes estaba el
  link "History" de Django) genera un `.docx` con esta bitácora completa
  — cada cambio de estado, quién lo hizo y su nota, notas de rechazo
  incluidas — en orden cronológico, hasta el estado actual del reporte
  (`expenses/history_export.py`, ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)).
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

### 21. Chat de ayuda flotante (`accounts/faq.py`, `accounts/help_chat_views.py`)
- Un widget flotante, animado, presente tanto en el portal del empleado
  como en el admin — mismo componente (`templates/help_chat/widget.html`),
  mismo backend, en ambos lados. Escondido por completo para visitantes
  no autenticados.
- **Deliberadamente basado en reglas, no en un LLM real** — ver
  [`docs/adr/0009-rule-based-help-chat.md`](docs/adr/0009-rule-based-help-chat.md)
  para el porqué: cada respuesta ya es un hecho documentado en algún lado
  de la app (el README, las pestañas Policies/Help), así que emparejar la
  pregunta con la respuesta correcta no necesita un modelo, una API key,
  costo por mensaje, ni conexión a internet — consistente con el resto de
  la app (SQLite por default, Bootstrap vendorizado, sin CDN).
- `accounts/faq.py:find_answer()` compara las palabras de la pregunta
  contra `FAQ_ENTRIES` (cada entrada con sus propias palabras clave) y
  devuelve la de mayor coincidencia — filtrado primero por rol
  (`audience: "all" | "employee" | "admin"`), para que un empleado nunca
  reciba una respuesta sobre gestionar Users & Groups, ni un admin reciba
  la respuesta de "cómo creo un reporte" en vez de la suya. Sin
  coincidencia, responde con un mensaje honesto de "no sé" en vez de
  inventar algo.
- **Se guarda en base de datos por cuenta, no por sesión**
  (`HelpChatMessage`, un row por mensaje, ligado al `User`) — tanto para
  empleados como para admins. La conversación sigue ahí la próxima vez
  que se abre el widget, en cualquier dispositivo, hasta que se reinicia
  explícitamente ("New chat" en el header del widget, que borra todos los
  mensajes de esa cuenta — `HelpChatResetView`).
- Tres endpoints bajo `/accounts/help-chat/` (`messages` GET, `ask` POST,
  `reset` POST), los tres con `LoginRequiredMixin` y escritos/leídos
  siempre contra `request.user` — nunca se puede ver ni borrar el chat de
  otra cuenta.
- **También responde preguntas de datos "en vivo" de RH**, no solo texto
  fijo (`DYNAMIC_ENTRIES` en `accounts/faq.py`, cada una con un
  `answer_fn(user)` en vez de una respuesta fija):
  - *"What's my employee number?"* — su propio número de empleado.
  - *"Who is my supervisor?"* — el supervisor de su reporte más reciente
    (el supervisor se captura por reporte, no es un campo del usuario).
  - *"Who owns the reports pending review?"* (solo admins) — lista en
    vivo de quién tiene reportes pendientes ahora mismo, con el mismo
    alcance por departamento que ya usa el Dashboard
    (`pending_reports_notification`) — un admin de departamento nunca ve
    nombres de otro departamento a través del chat tampoco.
  - *"What's my recent activity?"* — las últimas 5 entradas del audit log
    (`ExpenseReportAuditLog`) de sus propios reportes (creado, documento
    subido/borrado, enviado…), con fecha y en qué reporte. La versión para
    admins (*"What's the recent activity on reports I can see?"*) aplica
    el mismo alcance por departamento que la pregunta de arriba — nunca
    una forma nueva de ver más de lo que el Dashboard ya le mostraría.
  - Además, el tipo de gasto (Taxi/Meal/Flight/Hotel/Other) y el tipo de
    cambio USD/MXN que responde el chat se leen directamente de
    `TravelDocument.DocType` y `policies.USD_MXN_RATE` — nunca un número
    o lista duplicada a mano que se pudiera desincronizar del valor real.
- **También responde dudas generales del portal** ("what is this app
  for", "I'm lost") con una respuesta de una sola entrada FAQ que resume
  el flujo completo (crear reporte → adjuntar recibos → enviar → revisar
  → aprobar/rechazar) y sugiere qué más preguntar — pensada como el punto
  de entrada para alguien que no sabe ni por dónde empezar a preguntar.

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

- **`accounts/decorators.py:staff_permission`** — `ExpenseReportAdmin`
  tenía tres métodos (`has_module_permission`, `has_view_permission`,
  `has_change_permission`) con exactamente el mismo cuerpo de dos líneas.
  Ahora es un solo decorador aplicado a los tres. Vive en `accounts/` (no
  en `expenses/admin/`, donde empezó) porque `accounts/admin.py` también
  lo usa ahora: `UserAdmin`/`GroupAdmin` (re-registrado) lo aplican a sus
  cinco métodos `has_*_permission`, para que Users &amp; Groups deje de
  ser exclusivo del admin general (`is_superuser`) y cualquier cuenta
  `is_staff` — Adrian Heymes (admin de departamento) incluido — pueda
  ver y gestionar cuentas y grupos.
- **`expenses/views/decorators.py:draft_only`** — `UploadDocumentView` y
  `DeleteDocumentView` repetían el mismo guard ("solo mientras el reporte
  sigue en `draft`") con distinto mensaje. El decorador lo centraliza y de
  paso les pasa el reporte ya cargado (`report=`), sin que cada vista tenga
  que volver a pedirlo.

### Interfaz enterprise (Separated Interface / Strategy)

`expenses/exporters.py` define una interfaz formal (`ReportExporter`, una
`ABC` con `build()` abstracto) para los formatos exportables — antes,
`services.py:finalize_approval` y `views/exports.py` repetían, una vez por
formato, la misma ceremonia de "generar a `BytesIO`, leer los bytes,
guardar/servir" (4 bloques casi idénticos entre los dos archivos), y el
content-type de Word estaba además hardcodeado por segunda vez en
`views/exports.py`. Ahora esos puntos de uso pasan por `excel_exporter` /
`word_exporter`; agregar un formato adicional es agregar una clase en
`exporters.py`, no tocar `services.py` ni las vistas — así se agregó
`HistoryExporter` (`expenses/history_export.py`), el tercer formato: a
diferencia de los otros dos nunca es un snapshot guardado, siempre se
genera al vuelo a partir de `report.audit_log` — es lo que descarga el
botón "Download history" del panel de un reporte (ver
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)).

Esto formaliza un patrón que la app ya seguía en espíritu — el **Service
Layer** de Fowler (`expenses/services.py`, lógica de negocio fuera de
vistas/admin) y los **Policy objects** (`expenses/policies.py`,
`validators.py`) ya son ejemplos de "programar contra una interfaz/
separación de responsabilidades", típicos de arquitectura enterprise —
`exporters.py` es la primera vez que esa interfaz se declara explícitamente
con una clase abstracta en vez de solo por convención de nombres.

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para el diagrama de
arquitectura del sistema completo y para cómo está armado el panel de
admin en concreto: los tabs del Dashboard, los tabs de la página de
revisión de un reporte (cómo funciona la clasificación de fieldsets por
JS), y los context processors detrás de cada uno. Cada decisión de
arquitectura importante (por qué monolito, por qué SQLite/Postgres, el
modelo de acceso de admin, etc.) tiene su propio registro en
[`docs/adr/`](docs/adr/) — contexto, alternativas consideradas, y
consecuencias, no solo la decisión final. Y
[`docs/USER_STORIES.md`](docs/USER_STORIES.md) consolida todo el proyecto
como historias de usuario por rol (empleado, admin de departamento, admin
general, operador de la infraestructura).

## Estructura

```
lab2/
  manage.py
  Dockerfile                    # imagen para desplegar en servidor de intranet — ver docs/DEPLOYMENT.md
  docker-compose.yml             # levanta la imagen con datos persistentes en un volumen
  .dockerignore
  .env.example                 # variables de entorno documentadas (copiar a .env)
  docs/DATA_MODEL.md            # diagrama ER y trazabilidad
  docs/DEPLOYMENT.md             # contenedores, HTTPS, base de datos, CI, despliegue en intranet y en la nube
  docs/ARCHITECTURE.md           # diagrama de arquitectura del sistema + cómo está armado el panel de admin
  docs/USER_STORIES.md           # historias de usuario por rol, consolidando todo el proyecto
  docs/adr/                     # Architecture Decision Records — una por decisión de arquitectura, con alternativas y consecuencias
  config/                       # settings (django-environ, AUTO_SHUTDOWN_HOURS, branding, email/lockout), urls, wsgi/asgi
  accounts/
    models.py                    # User (+ employee_number, supervised_department), LoginEvent, find_user_by_login_identifier()
    backends.py                    # EmployeeNumberOrEmailBackend — login con email o número de empleado
    decorators.py                  # staff_permission — compartido por accounts/admin.py y expenses/admin/reports.py
    signals.py                    # graba LoginEvent en cada intento de login
    security.py                    # is_account_locked() — bloqueo tras 3 fallos
    context_processors.py          # notificaciones (pendientes, aprobado/rechazado), tabla de reportes del dashboard, donut chart
    server_lifecycle.py            # apagado automático del runserver a las 12h
    forms.py                       # LoginForm/AdminLoginForm/reset — LockoutCheckMixin
    views.py                       # SignUpView, PasswordResetConfirmView (CBVs)
    admin.py                       # UserAdmin, GroupAdmin (re-registrado), LoginEventAdmin (solo lectura) — StaffManagedAdminMixin
    faq.py                          # FAQ_ENTRIES + find_answer() — motor del chat de ayuda
    help_chat_views.py              # HelpChatHistoryView/AskView/ResetView — /accounts/help-chat/*
    migrations/0002_seed_admin.py
    migrations/0005_backfill_employee_numbers.py
    migrations/0007_seed_org_admins.py   # Iris Cortez (RH) + Adrian Heymes (ICS)
    migrations/0008_seed_axel_mhp_employee.py  # Axel Valenzuela, identidad de dominio MHP (empleado, no admin)
    migrations/0009_seed_karen_admin.py     # Karen Plascencia (RH)
    migrations/0010_seed_steffan_widmer.py  # Steffan Widmer, CEO (RH)
    migrations/0011_helpchatmessage.py      # modelo del chat de ayuda
    tests/                          # un archivo por concepto: signup, security, org_admin_seed,
                                     # department_scoping, notifications, approval_chart, server_lifecycle,
                                     # employee_number_login, help_chat...
  expenses/
    models.py                  # ExpenseReport (+ excel/word_snapshot), TravelDocument, AuditLog
    policies.py                 # DAILY_LIMIT_USD, USD_MXN_RATE, SUBMISSION_WINDOW_DAYS, MAX_TRIP_SPAN_DAYS, CEO_NAME, validate_trip_span
    validators.py                # validate_file_size (genérico; el de páginas de PDF vive en pdf_analysis.py)
    pdf_analysis.py             # extracción de monto/tipo/fecha/proveedor/moneda (prioriza pág. 1-2) y límite de 4 páginas
    image_analysis.py            # chequeo de calidad de fotos (legible/nítida/tamaño) — sin OCR, ver docs/adr/0010
    services.py                  # build_travel_document + finalize_approval (exports y borrado de originales, al aprobar)
    exporters.py                  # ReportExporter (interfaz) + ExcelExporter/WordExporter/HistoryExporter — ver "Interfaz enterprise"
    naming.py                     # export_basename() — convención de nombre de RH (empleado, fecha, número, APROBADO)
    word_export.py                # genera el .docx (con capturas de recibos) al aprobar
    history_export.py             # genera el .docx de historial (auditoría completa) para el botón "Download history"
    views/                       # reports.py, documents.py, exports.py, mixins.py, decorators.py (draft_only) — ver arriba
    admin/                        # reports.py, approved_history.py, audit_log.py, forms.py, inlines.py, mixins.py — staff_permission ahora vive en accounts/decorators.py
    excel.py
    tests/                      # un archivo por vista/servicio probado — ver arriba
  templates/
    base.html                    # layout del portal del empleado (en inglés) + banner de notificaciones
    help_chat/widget.html          # widget flotante del chat de ayuda — incluido en base.html y admin/base_site.html
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

212 tests: reglas de transición de `ExpenseReport` (incluye deadline y
cláusula CEO), validación de rango de fechas del viaje (`validate_trip_span`),
límite de páginas de PDF y priorización de las primeras 2 páginas, política
de $60/día (incluida la excepción de vuelo/hotel), análisis de PDF (monto y tipo detectados, y el endpoint de
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
apagado automático del servidor a las 12h, el flujo de aprobación/rechazo
a través del Django Admin, la marca de días fuera de política directamente
sobre la tabla de gastos del Word (sin la tabla aparte que tenía antes), la
generación del `.docx` de historial (`HistoryExporter`/`history_export.py`)
con el orden cronológico correcto y las notas de rechazo incluidas, el
login con número de empleado (`EmployeeNumberOrEmailBackend`), que el
bloqueo por intentos fallidos cuenta igual sin importar qué identificador
se haya escrito en cada intento, la tabla Pending/Approved del Dashboard
con su alcance por departamento, y que Users &amp; Groups sea accesible
para cualquier cuenta `is_staff` (no solo `is_superuser`) incluyendo que
un admin de departamento pueda otorgarle acceso de admin a alguien más, y
el chat de ayuda (`find_answer()` respetando el filtro por rol, cada
endpoint (`help-chat/ask` / `messages` / `reset`) devolviendo solo los
mensajes de `request.user`, y que el widget solo se renderiza para
cuentas autenticadas).

Lo que estos tests **no** cubren (y por qué): el render visual del front-end
(nav responsive, estado "active" de los links, el badge de rol admin) — son
cambios de plantilla/CSS, no de lógica de negocio, así que se verificaron
manualmente (servidor local + smoke test) en vez de con aserciones
automatizadas sobre HTML.

## Despliegue en servidor de intranet (y en la nube)

La app se documenta y prueba como servidor de desarrollo local. Para
correrla en un servidor de intranet de la empresa se agregó soporte para
contenedores (`Dockerfile`, `docker-compose.yml`) y un pipeline de CI de
ejemplo (`.github/workflows/lab2-ci.yml`) — ver
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) para el cómo y el porqué
(incluye por qué se eligió contenedores sobre una instalación directa en el
servidor, la decisión de base de datos SQLite vs. PostgreSQL, y una
sección aparte sobre qué cambia — y qué se necesita agregar — para
desplegar esta misma imagen en Azure, AWS o GCP en vez de en el servidor
de intranet).
