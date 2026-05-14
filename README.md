# U-Ride 🚗 | Plataforma de Carpooling Universitario UTA

> Sistema web de transporte compartido **exclusivo para estudiantes** con correo institucional `@uta.edu.ec` verificado.

---

## 📋 Índice

1. [Stack Tecnológico](#-1-stack-tecnológico)
2. [Instalación y Configuración](#-2-instalación-y-configuración)
3. [Base de Datos MySQL](#-3-base-de-datos-mysql)
4. [Arquitectura del Proyecto](#-4-arquitectura-del-proyecto)
5. [Módulos y Funcionalidades](#-5-módulos-y-funcionalidades)
6. [Sistema de Autenticación y Email](#-6-sistema-de-autenticación-y-email)
7. [Gestión de Viajes](#-7-gestión-de-viajes)
8. [Sistema de Seguridad](#-8-sistema-de-seguridad)
9. [Panel de Administración](#-9-panel-de-administración)
10. [API REST](#-10-api-rest)
11. [Frontend y Diseño](#-11-frontend-y-diseño)
12. [Tests](#-12-tests)
13. [Solución de Problemas](#-13-solución-de-problemas)
14. [Despliegue en Producción (Render + Aiven)](#-14-despliegue-en-producción-render--aiven)

---

## 🛠 1. Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| **Backend** | Flask (Python) | 2.3.3 |
| **Base de Datos** | MySQL única — PyMySQL | 8.x |
| **ORM** | SQLAlchemy + Flask-Migrate | 3.1.1 |
| **Autenticación** | Flask-Login + itsdangerous | 0.6.2 |
| **Formularios** | Flask-WTF + WTForms | 1.1.1 |
| **Email** | API HTTP (Google Apps Script) para evadir bloqueo Render | — |
| **Frontend** | Jinja2 + Bootstrap 5 + Font Awesome 6 | — |
| **Mapas** | Leaflet.js + OpenStreetMap + OSRM | 1.9.4 |
| **Seguridad** | Werkzeug hashing + CSRF + tokens firmados | — |

> ⚠️ **Esta aplicación usa exclusivamente MySQL.** No hay soporte para SQLite.

---

## 🚀 2. Instalación y Configuración

### Requisitos Previos
- Python 3.10+
- MySQL 8.x activo (XAMPP/WAMP/instalación directa)
- pip (gestor de paquetes Python)

### Paso a Paso

```bash
# 1. Abrir el proyecto
cd "APP modelado de software Proyecto"

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # Linux/Mac

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear la base de datos MySQL (ver sección 3)

# 6. Ejecutar servidor
python run.py
```

La aplicación estará disponible en: **http://127.0.0.1:5000**

### Credenciales por Defecto
| Rol | Email | Contraseña |
|-----|-------|-----------|
| Administrador | `admin@uta.edu.ec` | `admin123` |

---

## 🗄 3. Base de Datos MySQL

### 3.1 Crear la Base de Datos

Abre phpMyAdmin (o consola MySQL) y ejecuta:

```sql
CREATE DATABASE u_ride_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.2 Configurar Conexión en `.env`

```env
# Formato: mysql+pymysql://usuario:contraseña@host:puerto/nombre_bd
DATABASE_URL=mysql+pymysql://root:@localhost:3307/u_ride_db
```

| Parámetro | Valor por defecto | Descripción |
|-----------|-----------------|-------------|
| `usuario` | `root` | Usuario MySQL |
| `contraseña` | *(vacío)* | Contraseña root (cambiar en producción) |
| `host` | `localhost` | Servidor MySQL |
| `puerto` | `3307` | Puerto MySQL (XAMPP usa 3307) |
| `nombre_bd` | `u_ride_db` | Base de datos a usar |

> Si tu MySQL usa otro puerto (ej. `3306` en instalaciones directas), cambia el puerto en `.env`.

### 3.3 Tablas del Sistema (7 tablas)

Las tablas se crean **automáticamente** al ejecutar `python run.py`:

| Tabla | Descripción | Campos Principales |
|-------|-------------|-------------------|
| `usuarios` | Cuentas de estudiantes y admin | email, nombre, dirección (geolocalizada), teléfono emergencia, reputación, estado |
| `viajes` | Viajes publicados por conductores | origen, destino, fecha_hora, cupos, estado |
| `solicitudes` | Peticiones para unirse a viajes | viaje_id, pasajero_id, estado |
| `calificaciones` | Valoraciones entre usuarios | puntuación (1-5), comentario |
| `reportes` | Reportes de conducta indebida | motivo, evidencia, tipo_sanción |
| `eventos_trazabilidad` | Log de auditoría (RNF4) | acción, usuario, viaje, timestamp |
| `mensajes` | Chat entre conductor y pasajero | contenido, leído |

### 3.4 Diagrama de Relaciones

```
usuarios ──1:N──▶ viajes (conductor)
usuarios ──1:N──▶ solicitudes (pasajero)
viajes   ──1:N──▶ solicitudes
viajes   ──1:N──▶ calificaciones
viajes   ──1:N──▶ mensajes
usuarios ──1:N──▶ reportes (reportante/reportado)
usuarios ──1:N──▶ eventos_trazabilidad
```

---

## 📁 4. Arquitectura del Proyecto

```
APP modelado de software Proyecto/
├── run.py                         # Punto de entrada — solo MySQL
├── config.py                      # Configuración (Development/Testing/Production)
├── .env                           # Variables de entorno (DATABASE_URL, SMTP, SECRET_KEY)
├── requirements.txt               # Dependencias Python
├── test_email.py                  # Script diagnóstico SMTP independiente
│
├── app/                           # ══ BACKEND ══
│   ├── __init__.py                # Fábrica de app Flask (valida MySQL obligatorio)
│   ├── models.py                  # 7 modelos de datos (SQLAlchemy)
│   ├── forms.py                   # Formularios WTForms (validación dominio @uta.edu.ec)
│   ├── init_db.py                 # Crea usuario admin inicial
│   │
│   ├── auth/routes.py             # Login, registro, verificar email, recuperar password
│   ├── auth/utils.py              # Envío de emails via smtplib directo (UTF-8)
│   ├── main/routes.py             # Dashboard, perfil
│   ├── viajes/routes.py           # CRUD viajes, solicitudes, chat
│   ├── viajes/services.py         # Lógica de negocio de viajes
│   ├── seguridad/routes.py        # Calificar, reportar
│   ├── seguridad/reputation.py    # Algoritmo de reputación
│   ├── admin/routes.py            # Panel administrativo
│   └── api/routes.py              # API REST JSON
│
├── frontend/                      # ══ FRONTEND ══
│   ├── static/css/style.css       # Estilos del sistema
│   ├── static/js/main.js          # JavaScript general
│   ├── static/js/mapa.js          # Integración Leaflet
│   └── templates/                 # 20+ plantillas Jinja2
│       ├── base.html              # Layout principal (sidebar + topbar)
│       ├── auth/                  # login, registro, verificar, recuperar, reset_password
│       ├── viajes/                # Buscar, publicar, detalle, mis viajes
│       ├── seguridad/             # Calificar, reportar, reglas
│       ├── admin/                 # Dashboard, reportes, usuarios, stats
│       └── errors/                # 404, 500
│
└── tests/                         # Tests unitarios e integración (MySQL)
```

---

## 🔑 5. Módulos y Funcionalidades

### Módulo Auth (`/auth`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/auth/login` | GET/POST | Inicio de sesión con correo institucional verificado |
| `/auth/registro` | GET/POST | Registro solo con `@uta.edu.ec` |
| `/auth/logout` | GET | Cerrar sesión |
| `/auth/verificar/<token>` | GET | Verificar email con token firmado (24h) |
| `/auth/verificar-enviado` | GET | Página informativa post-registro |
| `/auth/reenviar-verificacion` | GET/POST | Reenviar email de verificación |
| `/auth/recuperar` | GET/POST | Solicitar recuperación de contraseña |
| `/auth/reset-password/<token>` | GET/POST | Restablecer contraseña (token 1h) |

### Módulo Principal (`/`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Dashboard con viajes recientes |
| `/perfil` | GET | Ver perfil del usuario con mapa estático |
| `/perfil/editar` | GET/POST | Editar información personal, autocompletado de direcciones (Nominatim) y mapa interactivo (Leaflet.js) |


### Módulo Viajes (`/viajes`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/viajes/buscar` | GET/POST | Buscar viajes con filtros |
| `/viajes/publicar` | GET/POST | Publicar nuevo viaje |
| `/viajes/detalle/<id>` | GET | Detalle del viaje + mapa + chat |
| `/viajes/mis-viajes` | GET | Viajes como conductor y pasajero |
| `/viajes/solicitar/<id>` | POST | Solicitar unirse a un viaje |
| `/viajes/gestionar/<id>/<accion>` | POST | Aceptar/rechazar solicitud |
| `/viajes/enviar-mensaje/<v>/<d>` | POST | Enviar mensaje en chat |
| `/viajes/cancelar/<id>` | POST | Cancelar viaje (2h anticipación) |
| `/viajes/finalizar/<id>` | POST | Finalizar viaje |

### Módulo Seguridad (`/seguridad`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/seguridad/reglas-seguridad` | GET | Normas de convivencia |
| `/seguridad/calificar/<v>/<d>` | GET/POST | Calificar usuario (1-5 ⭐) |
| `/seguridad/reportar/<id>` | GET/POST | Reportar usuario |

### Módulo Admin (`/admin`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/admin/dashboard` | GET | Panel de control |
| `/admin/reportes` | GET | Gestionar reportes |
| `/admin/reportes/<id>/resolver` | POST | Resolver: advertir/suspender/OK |
| `/admin/usuarios` | GET | Lista de usuarios |
| `/admin/usuarios/<id>/suspender` | POST | Suspender/activar cuenta |
| `/admin/estadisticas` | GET | Estadísticas del sistema |

---

## 🔐 6. Sistema de Autenticación y Email

### Flujo Completo

```
[REGISTRO]
  Usuario llena formulario (nombre, apellido, @uta.edu.ec, password)
          │
          ▼
  Validación en forms.py:
    ¿Es @uta.edu.ec? ¿Email no duplicado? ¿Password ≥ 8 chars?
          │
          ▼
  Cuenta creada (email_verificado=False)
          │
          ▼
  Token firmado con itsdangerous (24h) → Email enviado vía SMTP

[VERIFICACIÓN]
  Usuario abre enlace /auth/verificar/<token>
          │
          ▼
  email_verificado = True → Puede iniciar sesión

[LOGIN]
  Correo + contraseña → email_verificado=True + esta_activo=True → Acceso

[RECUPERACIÓN]
  POST /auth/recuperar (correo @uta.edu.ec)
          │
          ▼
  Token de recuperación (1h) → Email enviado con enlace de reset
          │
          ▼
  GET/POST /auth/reset-password/<token> → nueva contraseña → login
```

### Reglas de Seguridad
- ✅ Solo correo institucional `@uta.edu.ec` puede registrarse
- ✅ Correo debe ser verificado antes de hacer login
- ✅ Contraseña mínima 8 caracteres (hash con Werkzeug pbkdf2)
- ✅ Tokens firmados con `itsdangerous` (24h verificación / 1h recuperación)
- ✅ Cuentas suspendidas no pueden iniciar sesión
- ✅ Protección CSRF en todos los formularios (Flask-WTF)
- ✅ Protección contra Open Redirect en login
- ✅ Mensajes genéricos en recuperación (no revelan si el correo existe)

---

### 📧 Sistema de Email (SMTP)

El envío de correos usa `smtplib` de Python directamente — sin dependencias externas adicionales.

#### Decisiones técnicas importantes

| Decisión | Por qué |
|---|---|
| `sendmail()` + `as_string()` | Máxima compatibilidad con servidores institucionales (`@uta.edu.ec`) |
| HTML simple (sin tablas anidadas) | Evita filtros de spam — el servidor UTA bloquea HTML complejo |
| Sin `ehlo()` extra | Igual que `test_email.py` que funciona correctamente |
| Enlace siempre en consola | Respaldo si el email va a spam |

#### Flujo de recuperación con cuenta sin verificar

Antes existía un bug circular: si la cuenta no estaba verificada, el formulario de recuperación no enviaba nada (condición `email_verificado=True`). Ahora:

```
/auth/recuperar → cuenta verificada   → envía email de recuperación
               → cuenta SIN verificar → envía email de verificación (rompe el ciclo)
               → cuenta no existe     → mensaje genérico (no revela info)
```

#### Implementación técnica (`app/auth/utils.py`)

```python
# Igual que test_email.py — máxima compatibilidad
server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
server.starttls()
server.login(username, password)
server.sendmail(username, [destinatario], msg.as_string())
```

> **Nota:** Se probó `send_message()` pero genera headers que el servidor `@uta.edu.ec` filtra como spam. Se usa `sendmail()` + `as_string()` que es idéntico al script de prueba que sí funciona.

#### Modo Desarrollo — Sin SMTP configurado

Cuando `MAIL_USERNAME` no está configurado en `.env`, los **tokens se imprimen en la consola del servidor**:

```
=================================================================
  [U-Ride DEV] VERIFICACION DE CUENTA
  Usuario : Cesar <usuario@uta.edu.ec>
  Enlace  : http://127.0.0.1:5000/auth/verificar/eyJhbGc...
  Validez : 24 horas
=================================================================

=================================================================
  [U-Ride DEV] RECUPERACION DE CONTRASENA
  Usuario : Cesar <usuario@uta.edu.ec>
  Enlace  : http://127.0.0.1:5000/auth/reset-password/eyJhbGc...
  Validez : 1 hora
=================================================================
```

Copia ese enlace y pégalo en el navegador para verificar o restablecer.

#### Configurar Gmail SMTP (envío real de correos)

**Paso 1** — Activa verificación en 2 pasos en tu cuenta Gmail:
[https://myaccount.google.com/security](https://myaccount.google.com/security)

**Paso 2** — Genera una Contraseña de App:
[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

→ Escribe un nombre (ej: `URide`) → clic **Crear** → copia los 16 caracteres que aparecen

**Paso 3** — Configura el archivo `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=abcdefghijklmnop    # 16 caracteres SIN espacios
MAIL_DEFAULT_SENDER=U-Ride <tu_correo@gmail.com>
```

> El puerto 587 usa **TLS** (no SSL). La app lo configura automáticamente con `MAIL_USE_TLS=True` y `MAIL_USE_SSL=False`.

**Paso 4** — Verifica la conexión SMTP antes de reiniciar el servidor:

```powershell
venv\Scripts\python test_email.py tu_correo@uta.edu.ec
```

Si muestra `✅ ¡CORREO ENVIADO EXITOSAMENTE!` → reinicia el servidor y los correos se enviarán automáticamente desde la web.

**Paso 5** — Reinicia el servidor. Al arrancar verás:

```
  ✉️  Email SMTP activo: tu_correo@gmail.com
```

Eso confirma que el SMTP está activo y los correos llegarán reales.

---

## 🚗 7. Gestión de Viajes

### Ciclo de Vida de un Viaje

```
Publicar (abierto) ──▶ Recibir solicitudes ──▶ Aceptar pasajeros
     │                                              │
     │ (cupos llenos)                               ▼
     └────────▶ completo ──▶ en_curso ──▶ finalizado
                                              │
                              Cancelar (2h) ──▶ cancelado
```

### Estados del Viaje
| Estado | Significado |
|--------|------------|
| `abierto` | Tiene cupos disponibles |
| `completo` | Todos los cupos ocupados |
| `en_curso` | Viaje en progreso |
| `finalizado` | Viaje completado, se puede calificar |
| `cancelado` | Viaje cancelado por el conductor |

### Sistema de Mapas
- **OpenStreetMap** para los tiles del mapa
- **OSRM** para calcular rutas reales por carretera
- **Geolocalización del navegador** para trasladar coordenadas
- **Animación** del vehículo moviéndose por la ruta
- **11 zonas predefinidas** con coordenadas base

---

## ⭐ 8. Sistema de Seguridad

### Reputación
- Calificaciones de 1 a 5 estrellas después de cada viaje finalizado
- Promedio calculado automáticamente al calificar
- Niveles: Excelente (≥4.5), Bueno (≥3.5), Regular (≥2.5), Precaución (<2.5)
- Mínimo 5 calificaciones para salir de "Nuevo usuario"

### Reportes
- Motivos: comportamiento inapropiado, cancelación tardía, falta de respeto, incumplimiento
- Evidencia opcional (URL de captura de pantalla)
- Sanciones: advertencia, suspensión, o sin sanción

---

## 👑 9. Panel de Administración

Accesible solo para usuarios con `es_admin = True`.

| Funcionalidad | Descripción |
|--------------|-------------|
| Dashboard | Totales de usuarios, viajes, reportes pendientes |
| Gestionar Reportes | Advertir, suspender o resolver sin sanción |
| Gestionar Usuarios | Ver lista, suspender/activar cuentas |
| Estadísticas | Métricas completas del sistema |

---

## 📡 10. API REST

Base URL: `/api/v1`

| Endpoint | Método | Respuesta |
|----------|--------|-----------|
| `/api/v1/viajes` | GET | Lista viajes abiertos (JSON) |
| `/api/v1/viajes/<id>/mapa` | GET | Datos geográficos para Leaflet |
| `/api/v1/zonas` | GET | Zonas con coordenadas |
| `/api/v1/estadisticas` | GET | Métricas globales |
| `/api/v1/perfil/mis-viajes` | GET | Viajes del usuario autenticado |

---

## 🎨 11. Frontend y Diseño

### Paleta de Colores
| Color | Hex | Uso |
|-------|-----|-----|
| Rojo principal | `#dc2626` | Accent, botones, sidebar activo |
| Negro sidebar | `#111827` | Fondo sidebar y conductor card |
| Gris fondo | `#f5f6fa` | Fondo principal |
| Blanco | `#ffffff` | Tarjetas |

### Tipografía
- **Inter** (Google Fonts) — pesos 400, 600, 700, 800

### Layout y Responsividad (Mobile First)
- Diseño 100% responsivo adaptable a **Celulares, Tablets y Laptops**.
- Sidebar fija (240px) en escritorio.
- En móviles (≤ 768px): La barra lateral se oculta completamente fuera de pantalla (slide-out) para maximizar el área de uso. Menú "hamburguesa" deslizable.
- Tarjetas de estadísticas y formularios adaptables apilables (Stacking) en pantallas pequeñas.
- Topbar sticky con título de página.
- **Backdrop Móvil:** Capa de fondo semi-transparente para cerrar el menú lateral en móviles al tocar fuera.
- **Botones Adaptables:** Botones que se expanden a ancho completo en dispositivos pequeños para mejorar la usabilidad.

---

## 🧪 12. Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Solo modelos
python -m pytest tests/test_models.py -v

# Solo rutas
python -m pytest tests/test_routes.py -v
```

> Los tests usan la configuración `testing` que también apunta a MySQL (`u_ride_db`).

### Tests Disponibles
**Modelos (7):** Creación usuario, contraseña, nivel confianza, viaje, solicitud/aceptación, viaje lleno, calificación, reportes.

**Rutas (7):** Página inicio, login, registro, registro válido, login inválido, ruta protegida, error 404.

---

## ⚡ Comandos Rápidos

```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Ejecutar servidor (MySQL debe estar activo)
python run.py

# Probar SMTP desde terminal
venv\Scripts\python test_email.py correo@uta.edu.ec

# Crear admin manualmente
flask create-admin

# Inicializar BD (crea tablas + admin)
flask init-db

# Ejecutar tests
python -m pytest tests/ -v

# Reset rápido (Windows)
LIMPIAR_Y_REINICIAR.bat
```

---

## 🔧 13. Solución de Problemas

### Email no llega al destinatario
| Síntoma | Causa | Solución |
|---------|-------|----------|
| Consola muestra `[U-Ride DEV]` | `MAIL_USERNAME` no configurado en `.env` | Configura credenciales SMTP (ver sección 6) |
| `SMTPAuthenticationError` | Contraseña de app incorrecta o expirada | Genera nueva en [apppasswords](https://myaccount.google.com/apppasswords) |
| El correo va a SPAM | Servidor institucional filtra el remitente | Marcar como "No es spam" en `@uta.edu.ec` |
| Consola dice `>> Correo enviado` pero no llega | Spam en `@uta.edu.ec` | Revisar carpeta Correo No Deseado |

### No puedo verificar — ya estoy registrado
Si ya existe la cuenta pero no la verificaste, NO intentes registrarte de nuevo. Usa:
```
http://127.0.0.1:5000/auth/recuperar
```
Ingresa tu email `@uta.edu.ec`. Si la cuenta no está verificada, el sistema enviará automáticamente el **correo de verificación**.

### Error: "Unknown column 'usuarios.apellido'"
```sql
USE u_ride_db;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS apellido VARCHAR(100) DEFAULT '' AFTER nombre;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS genero VARCHAR(10) DEFAULT '' AFTER apellido;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL AFTER genero;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS direccion VARCHAR(200) DEFAULT '' AFTER fecha_nacimiento;
```

### Error: "Can't connect to MySQL"
1. Verifica que MySQL esté activo (XAMPP → Start MySQL)
2. Verifica el puerto en `.env` — XAMPP usa `3307`, instalación directa usa `3306`
3. Verifica que la base de datos `u_ride_db` exista

### Error: "RuntimeError — SOLO funciona con MySQL"
La URL `DATABASE_URL` en `.env` no apunta a MySQL. Verifica que contenga `mysql+pymysql://`.

### Errores en rojo en VSCode (Pylance)
Selecciona el intérprete correcto:
`Ctrl+Shift+P` → **Python: Select Interpreter** → `.\venv\Scripts\python.exe`

---

## ☁️ 14. Despliegue en Producción (Render + Aiven)

El proyecto está configurado y optimizado para ser desplegado de forma gratuita en la nube usando **Render.com** para el servidor web y **Aiven** para la base de datos MySQL.

### Características del Despliegue:
- **Gunicorn:** Se agregó `gunicorn` al `requirements.txt` como servidor WSGI listo para producción.
- **Creación de Tablas Automática:** El archivo `run.py` fue modificado para ejecutar `db.create_all()` automáticamente cuando Gunicorn inicializa la aplicación, garantizando que Aiven tenga las tablas listas al instante.
- **Blueprint Render:** Se incluye `render.yaml` como plantilla para despliegue automatizado.
- **Escucha Global:** La aplicación se enlaza a `0.0.0.0` para poder exponer el puerto correctamente en el contenedor de Render.

### Pasos Rápidos de Despliegue:
1. Subir el repositorio completo a GitHub.
2. Crear un servicio de base de datos **MySQL 8** gratuito en [Aiven](https://aiven.io/mysql).
3. Obtener la `Service URI` de Aiven y prefijarla con `+pymysql` (Ej: `mysql+pymysql://avnadmin:password@host...`).
4. En **Render.com**, crear un nuevo *Web Service* conectado al repositorio de GitHub.
5. Configurar el *Build Command*: `pip install -r requirements.txt`
6. Configurar el *Start Command*: `gunicorn run:app`
7. Agregar las Variables de Entorno en Render:
   - `DATABASE_URL` = URL de Aiven (mysql+pymysql://...)
   - `PYTHON_VERSION` = 3.10.0
   - `SECRET_KEY` = (Una clave larga de seguridad)
   - `FLASK_ENV` = production
8. Hacer deploy. La aplicación estará viva en un enlace `.onrender.com`.

### 🚨 IMPORTANTE: Sistema de Correos (Bypass de Render)
**Render (Capa Gratuita) bloquea todo el tráfico saliente SMTP (puertos 25, 465, 587).**
Por esta razón, la aplicación ya NO usa `smtplib` ni contraseñas de aplicación de Google. En su lugar, utiliza un **Webhook HTTP (Google Apps Script)** creado por el administrador. 

- El código en `app/auth/utils.py` envía un JSON vía puerto 443 (HTTPS) a la API de Google Scripts.
- Google Apps Script recibe el JSON y despacha el correo usando la cuenta asociada (Ej. `steven...`).
- Esto garantiza el envío de correos tanto en entornos locales como en la nube gratuita de Render de forma instantánea.