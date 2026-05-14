# 🛡️ Documento de Defensa Técnica: Proyecto Web U-Ride

Este documento está diseñado como una **guía de defensa de la arquitectura y decisiones técnicas** tomadas en el desarrollo de la plataforma U-Ride. Detalla los componentes principales de seguridad, gestión de usuarios y despliegue en la nube, respondiendo al "qué", "cómo" y "por qué" de cada implementación tecnológica.

---

## 1. Sistema de Autenticación y Gestión de Usuarios

El módulo de autenticación de U-Ride fue construido priorizando la seguridad y la exclusividad universitaria. Se construyó utilizando **Flask-Login** para el manejo de sesiones y **Werkzeug Security** para el encriptado de contraseñas.

### 1.1. Registro de Usuarios
- **Restricción de Dominio:** El registro está limitado exclusivamente a estudiantes universitarios. Para lograr esto, se implementó un validador personalizado en WTForms que rechaza cualquier correo electrónico que no termine exactamente en `@uta.edu.ec`.
- **Protección de Datos:** Las contraseñas nunca se guardan en texto plano. Se utiliza el algoritmo de hash `pbkdf2:sha256` provisto por Werkzeug.
- **Flujo de Seguridad:** Al registrarse, la cuenta se crea en la base de datos con un campo booleano `email_verificado = False`. El usuario no puede iniciar sesión hasta validar la propiedad de ese correo institucional.

### 1.2. Verificación de Cuenta (Email)
- **Generación de Tokens Seguros:** Para verificar la cuenta, el backend genera un token encriptado utilizando la librería `itsdangerous`. Este token contiene el correo del usuario y tiene un tiempo de expiración estricto de **24 horas**.
- **Proceso:** Al acceder a la ruta `/auth/verificar/<token>`, el sistema desencripta el token. Si es válido y no ha expirado, cambia `email_verificado` a `True` en la base de datos MySQL, habilitando el acceso total a la plataforma.

### 1.3. Recuperación de Contraseña
- **Mitigación de Enumeración de Usuarios:** Si un usuario intenta recuperar la contraseña de un correo que no existe, el sistema muestra un mensaje genérico ("Si el correo existe, se ha enviado un enlace"). Esto previene que atacantes externos descubran correos institucionales registrados.
- **Token de Corta Duración:** Se utiliza el mismo sistema de `itsdangerous`, pero con una expiración mucho más estricta de **1 hora** para los enlaces de recuperación de contraseña.
- **Prevención de Bloqueos Circulares:** Si un usuario intenta recuperar una contraseña pero su cuenta aún no ha sido verificada, el sistema detecta esto y, en lugar de bloquear el proceso, envía inteligentemente un **correo de verificación** en su lugar.

### 1.4. Inicio de Sesión (Login)
- **Validación Doble:** Al intentar iniciar sesión, el sistema verifica primero si la contraseña coincide (usando `check_password_hash`). Si es correcta, aplica una segunda validación: verificar si la cuenta está activa (`esta_activo = True`) y si el correo ha sido verificado.
- **Protección de Formularios:** Todo el proceso está protegido contra ataques CSRF (Cross-Site Request Forgery) mediante tokens únicos ocultos en los formularios de `Flask-WTF`.

---

## 2. Infraestructura Cloud y Arquitectura

Desplegar una aplicación en capas gratuitas (Free Tiers) conlleva retos técnicos significativos, especialmente relacionados con bases de datos relacionales y el envío masivo de correos institucionales.

### 2.1. Despliegue del Servidor Web (Render)
- **Tecnología:** Se optó por **Render.com** debido a su integración continua con GitHub.
- **Servidor WSGI:** En lugar del servidor de desarrollo de Flask (que no soporta concurrencia), se configuró **Gunicorn** (`gunicorn run:app`). Esto permite manejar múltiples peticiones simultáneas, un requisito crítico para aplicaciones web reales.
- **Auto-migraciones:** Se programó el archivo principal (`run.py`) para que detecte si faltan columnas en la base de datos y ejecute comandos `ALTER TABLE` automáticamente antes de que Gunicorn abra el puerto. Esto evita caídas del servidor por desincronización de modelos de datos tras una actualización de código.

### 2.2. Base de Datos en la Nube (Aiven MySQL)
- **Por qué Aiven:** Render no ofrece bases de datos MySQL persistentes y gratuitas a largo plazo. Se eligió **Aiven** porque proporciona instancias MySQL 8.x altamente disponibles.
- **Seguridad de Conexión:** Aiven obliga al uso de conexiones cifradas. Se configuró SQLAlchemy para inyectar los parámetros de conexión SSL (`ssl_mode: REQUIRED`) junto con el driver `PyMySQL`, garantizando que la transferencia de información (como contraseñas o chats) desde Render hacia Aiven esté 100% encriptada de extremo a extremo.

### 2.3. Bypass del Sistema de Correos (Google Apps Script)
Esta es una de las soluciones técnicas más destacadas del proyecto.
- **El Problema:** La capa gratuita de Render **bloquea todo el tráfico saliente** en los puertos estándar de correo electrónico (25, 465, 587) para evitar que sus servidores sean usados para enviar SPAM. Esto rompía el envío de tokens institucionales.
- **La Solución (Webhook API):** En lugar de que Flask envíe el correo, Flask actúa como un cliente API. Se configuró el backend en Python para hacer un `POST HTTP` (por el puerto seguro 443) hacia un **Google Apps Script** creado por nosotros.
- **Flujo Final:** Flask genera el JSON con el destinatario y el mensaje $\rightarrow$ Se envía a la URL secreta de Google Apps Script $\rightarrow$ Google recibe los datos y ejecuta `MailApp.sendEmail()`, utilizando los servidores de Google para enviar el correo a la cuenta institucional de la UTA.
- **Beneficio:** Esta arquitectura de microservicios evadió las restricciones de Render con un 100% de efectividad de entrega, asegurando que correos críticos nunca caigan en el olvido.

### 2.4. Verificación en 2 Pasos (Configuración del Correo Remitente)
- Si en algún momento se requiere usar el método tradicional de envío de correos (SMTP directo a través de Python en modo local o en un servidor de pago), se implementó la seguridad de Google.
- No se utilizan contraseñas normales para enviar correos institucionales automatizados. Se configuró la **Verificación en 2 Pasos de Google** en la cuenta emisora y se generó una **Contraseña de Aplicación** de 16 caracteres. Esta técnica es vital para evitar que Google marque los envíos del servidor como intentos de hackeo o inicios de sesión no autorizados.

---

## 3. Modernización e Interactividad del Perfil

El módulo de perfil de usuario evolucionó de un sistema rígido de selección a uno completamente dinámico y georreferenciado, mejorando enormemente la experiencia de usuario (UX).

### 3.1. API de Nominatim y Autocompletado
- Para evitar que los usuarios escriban direcciones falsas o ambiguas, se integró el motor de búsqueda de **OpenStreetMap (Nominatim API)** mediante JavaScript puro (Fetch API).
- A medida que el usuario escribe su dirección, el frontend solicita sugerencias reales de calles y lugares, mostrando una lista autocompletada.

### 3.2. Mapas Interactivos (Leaflet.js)
- Al seleccionar una dirección en el buscador, el sistema no solo guarda el texto, sino que extrae las **coordenadas geográficas exactas (Latitud y Longitud)**.
- Estas coordenadas se inyectan en un mapa interactivo construido con **Leaflet.js**. El usuario puede ver visualmente dónde está ubicada su residencia mediante un marcador.
- **Corrección manual:** El marcador fue configurado como "arrastrable" (`draggable: true`). Si la API geocodificó un punto inexacto, el usuario simplemente mueve el pin en el mapa, y las coordenadas se actualizan en los campos ocultos del formulario antes de presionar "Guardar".

### 3.3. Estructuración y Seguridad en Archivos
- El diseño web fue fragmentado en componentes de **Jinja2** (Herencia de plantillas con `base.html`), lo que permitió escalar la aplicación a más de 20 vistas sin repetir código estructural (como las barras de navegación).
- Para las imágenes de perfil, se configuraron rutas dinámicas relativas, asegurando que los archivos subidos estén protegidos por `secure_filename` (evitando vulnerabilidades de inyección de código) y aterricen explícitamente en el directorio estático público del frontend (`frontend/static/img/perfiles`), logrando un servicio de archivos seguro y rápido.
