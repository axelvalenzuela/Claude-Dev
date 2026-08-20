# Laboratorio 2 — Reportes de Gastos de Viaje

Aplicación web para que cada empleado suba sus documentos de viaje (vuelos,
hoteles, transporte...), arme un reporte de gastos y lo envíe a revisión. Un
único usuario administrador aprueba o rechaza los reportes; el empleado ve el
resultado en su propio portal. Cualquiera de los dos roles puede descargar el
reporte en Excel.

> Se evaluó inicialmente hacerlo en .NET/C#, pero por restricciones de
> permisos en el equipo de desarrollo se implementó en **Python + Django**,
> el mismo stack de base que el Laboratorio 1.

## Stack

- **Python 3.13 + Django 5** (vistas basadas en funciones, templates,
  sin frontend separado — mismo criterio de simplicidad que el Lab 1).
- **SQLite** vía el ORM de Django (`db.sqlite3`, cero dependencias externas).
- **Auth de Django** (modelo de usuario propio) para registro/login.
- **Django Admin** como panel de administrador — sin construir una interfaz
  aparte: es la forma idiomática de dar acceso restringido (`is_staff`) a
  una sola cuenta para aprobar/rechazar.
- **openpyxl** para generar los reportes `.xlsx`.
- **Test framework de Django** (basado en `unittest`) para las pruebas.

## Módulos implementados

### 1. Cuentas de usuario (`accounts/`)
- Modelo `User` propio (`AUTH_USER_MODEL = "accounts.User"`), extiende el
  usuario de Django agregando `department`. El username es el correo.
- **Registro** (`/accounts/signup/`): cualquiera puede crear una cuenta de
  empleado (nombre, departamento, correo, contraseña). Nunca queda con
  `is_staff`/`is_superuser`, así que jamás puede entrar al panel admin.
- **Login/Logout** (`/accounts/login/`, `/accounts/logout/`) con el sistema
  de sesiones de Django.
- Cada empleado ve **solo sus propios reportes**: todas las vistas de
  `expenses` filtran siempre por `request.user`.

### 2. Portal del empleado (`expenses/views.py`, `@login_required`)
- **Mis reportes** (`/reports/`): lista los reportes propios con estado
  (Borrador / En revisión / Aprobado / Rechazado), total y # de documentos.
- **Nuevo reporte** (`/reports/new/`): título + descripción, arranca en
  estado `draft`.
- **Detalle** (`/reports/<id>/`):
  - Subir documento de viaje (tipo, fecha, monto, archivo PDF/JPG/PNG) —
    solo mientras el reporte está en borrador.
  - Eliminar documentos (solo en borrador).
  - **Enviar a revisión**: pasa el reporte a `submitted` (requiere al menos
    un documento). A partir de aquí queda de solo lectura para el empleado.
  - Ver la nota y fecha de aprobación/rechazo una vez que el admin lo revisó.
  - **Descargar Excel** del reporte, en cualquier estado.

### 3. Panel de administrador — Django Admin (`expenses/admin.py`)
- No es una interfaz aparte hecha a mano: es `/admin/`, accesible solo para
  la cuenta sembrada con `is_staff=True` (ver abajo). Cualquier empleado
  normal que intente entrar es rechazado por el propio framework.
- **`ExpenseReportAdmin`** muestra únicamente reportes ya enviados (los
  borradores son privados del empleado, `get_queryset` los excluye).
- Cada reporte se abre en modo mayormente solo-lectura, con **dos campos
  editables**: `status` y `review_note` (nota de revisión). Los documentos
  se ven como inline de solo lectura, con link de descarga.
- Un `ModelForm` (`ExpenseReportAdminForm.clean`) valida la transición:
  solo se puede aprobar/rechazar un reporte `submitted`, y rechazar exige
  una nota con el motivo. Si no se cumple, el admin ve el error en el
  propio formulario.
- Al guardar con un cambio de `status`, se registran automáticamente
  `reviewed_at` y `reviewed_by` — el empleado ve el cambio de inmediato en
  su portal.
- También se registró `accounts.User` en el admin (con el campo
  `department` visible) para poder ver de un vistazo qué empleados existen.

### 4. Generación de Excel (`expenses/excel.py`)
- `build_report_workbook(report)` arma un `.xlsx` con: datos del empleado y
  departamento, título, estado, fecha de creación, nota de revisión (si
  aplica), y una tabla con cada documento (tipo, fecha, archivo, monto) más
  el total. La usan tanto el portal del empleado como el admin.

### 5. Documentos y almacenamiento (`expenses/models.py`)
- `TravelDocument.file` valida extensión (`.pdf`, `.jpg`, `.jpeg`, `.png`) y
  tamaño máximo (10 MB).
- Se guarda con un nombre físico único (`uuid4`) bajo
  `media/uploads/{user_id}/{report_id}/`, pero se conserva el nombre
  original (`original_filename`) para mostrarlo y para el nombre de
  descarga — así nunca se ve un nombre "raro" aunque dos archivos se
  llamen igual.

### 6. Reglas de negocio (testeadas, `expenses/models.py`)

El flujo de estados vive como métodos del propio modelo `ExpenseReport`
(`submit`, `approve`, `reject`), no en las vistas ni en el admin, para
poder probarlo sin pasar por HTTP:

```
draft --submit()--> submitted --approve()--> approved
                          \-----reject()----> rejected
```

- `submit()` exige al menos un documento y que el reporte esté en `draft`.
- `approve()`/`reject()` exigen que el reporte esté `submitted`.
- `reject()` exige una nota (motivo) no vacía.

### 7. Base de datos y siembra del admin (`accounts/migrations/0002_seed_admin.py`)

Una migración de datos (`RunPython`) crea, la primera vez que se corre
`migrate`, la única cuenta con acceso a `/admin/`. Los valores salen de
variables de entorno (con defaults de desarrollo si no se definen):

| Variable | Default local |
|---|---|
| `ADMIN_SEED_EMAIL` | `axel.valenzuela@uabc.edu.mx` |
| `ADMIN_SEED_PASSWORD` | `Admin#2026Local` |
| `ADMIN_SEED_NAME` | `Axel Valenzuela` |
| `ADMIN_SEED_DEPARTMENT` | `Administracion` |

> La contraseña por default es solo para desarrollo local. Cámbiala (o
> define las variables de entorno antes del primer `migrate`) si vas a
> correr esto fuera de tu máquina.

## Estructura

```
lab2/
  manage.py
  config/                # settings, urls, wsgi/asgi
  accounts/               # modelo de usuario, signup/login, admin de usuarios
    migrations/0002_seed_admin.py
  expenses/               # ExpenseReport, TravelDocument, vistas, excel.py, admin.py
    tests/                 # test_models, test_excel, test_views
  templates/base.html      # layout compartido (Bootstrap 5 vía CDN)
  static/css/site.css
  media/uploads/           # archivos subidos (no versionado)
  requirements.txt
```

## Cómo correrlo en local

Requiere **Python 3.13** (o 3.11+).

```bash
cd lab2
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

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

## Tests

```bash
cd lab2
python manage.py test
```

21 tests: reglas de transición de `ExpenseReport`, generación del Excel,
signup/aislamiento entre empleados, subida y envío de documentos, y el
flujo de aprobación/rechazo a través del Django Admin (incluyendo que un
empleado normal no puede entrar a `/admin/`).
