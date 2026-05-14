# 🧠 Knowledge Item (KI) — U-Ride Architecture & Restoration Guide

> **ATENCIÓN AGENTES IA:** Este documento sirve como "Memoria a largo plazo" (Knowledge Item) del proyecto U-Ride. Debe ser consultado antes de realizar modificaciones estructurales o si el usuario pide "restaurar" o "arreglar" el sistema tras un colapso en producción.

## 1. Topología del Sistema (Producción)
- **Servidor Web:** Render (Free Tier)
- **Base de Datos:** Aiven MySQL 8.x
- **Servicio de Correos:** Google Apps Script Webhook API (Bypass de Render)

## 2. Base de Datos (Aiven MySQL)
Render en capa gratuita no soporta bases de datos relacionales persistentes propias (PostgreSQL caduca a los 90 días). Por ello se usa Aiven.
- **Conector Crítico:** `mysql+pymysql://...`
- **Configuración SSL:** Requerida por Aiven. En `app/__init__.py`, la inicialización de SQLAlchemy inyecta explícitamente `connect_args={'ssl': {'ssl_mode': 'REQUIRED'}}`. Si se pierde esta configuración, el sistema colapsará con error 500 al registrar o iniciar sesión.
- **Aviso de Sincronización:** Los modelos de SQLAlchemy (ej. `usuarios.apellido`, `fecha_nacimiento`) fueron sincronizados manualmente en la base de datos de producción mediante consultas directas. Si se migra a otra BD, se DEBE ejecutar `flask init-db` y validar el esquema.

## 3. El Bypass de Email (El "Render Hack")
El problema más grave históricamente fue el **Error 502 / Timeouts** o fallos silenciosos al enviar correos institucionales de verificación (`@uta.edu.ec`).
- **La Causa:** Render (Free Tier) bloquea absolutamente todo el tráfico saliente TCP en los puertos SMTP (25, 465, 587).
- **La Solución:** Todo el módulo de correo clásico (`Flask-Mail` y `smtplib`) fue eliminado de `app/auth/utils.py`.
- **Implementación Actual:** Se hace un HTTP POST (Puerto 443) a un Google Apps Script creado por el administrador (`steven2001cesar@gmail.com`). 
- **Endpoint Secreto Activo:** `https://script.google.com/macros/s/AKfycbwwnd4Oaqby2NCP6JRHMMyzy0MWCXuTyMck4kHFECvQGC6-CC2URT5vePh9-pixUs9C/exec`
- **Formato del Payload:** JSON con `{ "to": destinatario, "subject": asunto, "html": html }`.

## 4. Estructura Crítica del Código
- `app/__init__.py`: Contiene el limpiador de URIs de Render y la configuración de SSL estricta para PyMySQL.
- `app/auth/utils.py`: Contiene el código de integración de `urllib.request` con Google Apps Script. 
- `config.py`: Fuerza `PREFERRED_URL_SCHEME = 'https'` en `ProductionConfig` para asegurar que los enlaces enviados en los correos tengan SSL válido, previniendo que los filtros antispam de la universidad reboten los correos.

## 5. Protocolo de Restauración
Si el sistema web se cae, revisa en este orden:
1. **Logs de Render:** Si marca `ETIMEDOUT` en peticiones, Aiven pudo haber pausado el servicio MySQL o cambiado la contraseña admin.
2. **Registro de Usuarios Roto:** Si el registro falla, revisa que la URI de base de datos en las Variables de Entorno de Render comience estrictamente con `mysql+pymysql://` (Render a veces sobreescribe esto y pone `mysql://` a secas, lo que crashea el ORM).
3. **Falla de Correos:** Si `urllib` da error 404, significa que el usuario borró o alteró el proyecto en Google Apps Script. Deberá crear uno nuevo y actualizar la constante `GOOGLE_SCRIPT_URL` en `app/auth/utils.py`.
