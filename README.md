# Lotengo

Aplicación web de objetos perdidos y encontrados, construida con Django 5.2.
El módulo inicial de cuentas incluye registro, acceso, verificación de correo,
restablecimiento de contraseña y aceptación de documentos legales.

## Estructura

- `lotengo/`: configuración Django y puntos de entrada WSGI/ASGI.
- `app/`: aplicaciones separadas por dominio funcional.
- `templates/`: plantillas compartidas y pantallas organizadas por módulo.
- `templates/componentes/`: barra de navegación, barra lateral y pie de página reutilizables.
- `static/css/` y `static/js/`: recursos separados por tipo y organizados según las carpetas de plantillas.
- `media/`: archivos cargados por usuarios; no versionar archivos subidos.

Aplicaciones preparadas: `cuentas`, `perfiles`, `publicaciones`, `categorias`, `ubicaciones`,
`busqueda`, `coincidencias`, `conversaciones`, `recuperaciones`, `pagos`, `notificaciones`,
`favoritos`, `denuncias`, `moderacion`, `auditoria` y `general`.

## Convención de pantallas y recursos

Cada pantalla vive en una carpeta de módulo. Su CSS y JavaScript mantienen la misma
jerarquía bajo las carpetas correspondientes:

```text
templates/usuarios/usuarios.html
templates/usuarios/modals/crear.html
static/css/usuarios/usuarios.css
static/css/usuarios/modals/crear.css
static/js/usuarios/usuarios.js
static/js/usuarios/modals/crear.js
```

Los componentes compartidos se guardan en `templates/componentes/` y sus recursos en
`static/css/componentes/` y `static/js/componentes/`. Las vistas usarán validación
explícita en las vistas o servicios; no se utilizarán formularios de Django.

Las pantallas de cuentas se agrupan por función y los recursos replican esas carpetas:

```text
templates/cuentas/acceso/reenviar_verificacion.html
templates/cuentas/recuperacion/restablecer_contrasena.html
templates/cuentas/legales/terminos.html
templates/cuentas/panel/panel.html
static/css/cuentas/acceso/reenviar_verificacion.css
static/js/cuentas/acceso/reenviar_verificacion.js
```

La plantilla compartida `base_cuentas.html` y sus recursos comunes permanecen directamente
en la carpeta `cuentas`.

## Módulo de publicaciones

`/publicaciones/` permite explorar avisos activos y filtrar por texto, tipo, categoría,
departamento y municipio. Las cuentas con correo verificado pueden crear avisos, adjuntar
fotografías, editar sus propios avisos, pausarlos y marcarlos como resueltos. Los datos
privados de verificación y las referencias exactas de ubicación solo se muestran a quien
creó el aviso.

Las categorías iniciales se cargan mediante migración. Las fotografías admiten JPG, PNG y
WEBP, con un máximo de cinco archivos de 5 MB cada uno; se renombran de forma aleatoria y
se guardan sin metadatos EXIF. La pantalla principal usa una tabla con acciones CRUD y
las páginas de crear, ver, editar y retirar están en `crud/`; retirar oculta el aviso
sin borrar el registro.

```text
templates/publicaciones/publicaciones.html
templates/publicaciones/crud/crear.html
templates/publicaciones/crud/detalle.html
templates/publicaciones/crud/editar.html
templates/publicaciones/crud/eliminar.html
static/css/publicaciones/publicaciones.css
static/css/publicaciones/crud/crear.css
static/js/publicaciones/publicaciones.js
static/js/publicaciones/crud/crear.js
```

CSS y JavaScript mantienen la misma estructura y nombres que sus plantillas.

## Configuración local

Requiere Python 3.11 o superior. `.env.example` contiene nombres de variables y
valores de muestra; `.env` es local y no se versiona. Si aún no tienes un `.env`,
cópialo desde la plantilla y completa sus valores:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configura la base de datos en `.env`. El proyecto permite SQLite (`DB_ENGINE=sqlite`)
o PostgreSQL (`DB_ENGINE=postgresql`). Para PostgreSQL, la base debe existir y estar
disponible en el host y puerto configurados.

Inicializa el sistema y crea la primera cuenta administrativa:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El correo de verificación y recuperación utiliza SMTP configurado en `.env`. Durante el
desarrollo local, con `DEBUG=True` y `PUBLIC_BASE_URL` vacío, los correos salen en texto
plano y los enlaces usan el host local de la solicitud. Para enviar correos con HTML y
enlaces utilizables fuera del equipo, define `PUBLIC_BASE_URL` con la URL pública HTTPS del
sitio. En producción, usa una clave secreta nueva, `DEBUG=False`, hosts permitidos y HTTPS;
no guardes credenciales reales en el repositorio.

Bootstrap 5.3 se carga desde jsDelivr en `templates/base.html`.

El modelo de usuario personalizado ya está definido en `app/cuentas`. Usa la migración inicial
incluida antes de crear datos en una base compartida.
