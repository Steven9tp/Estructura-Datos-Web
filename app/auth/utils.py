"""
Utilidades de autenticacion para U-Ride
=========================================
Usa smtplib directamente con send_message para soportar caracteres en español (ñ, tildes).
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

def _smtp_configurado() -> bool:
    """Verifica si las credenciales existen."""
    username = os.getenv('MAIL_USERNAME', '').strip()
    password = os.getenv('MAIL_PASSWORD', '').strip()
    return bool(username and password and len(password) >= 16)

def _enviar_smtp(destinatario: str, asunto: str, html: str, texto: str) -> bool:
    """Lógica robusta y síncrona que usa send_message para caracteres Unicode."""
    server_host = os.getenv('MAIL_SERVER', 'smtp.gmail.com').strip()
    server_port = int(os.getenv('MAIL_PORT', 465)) # Usar 465 por defecto para SSL
    username    = os.getenv('MAIL_USERNAME', '').strip()
    password    = os.getenv('MAIL_PASSWORD', '').strip()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From']    = f"U-Ride <{username}>"
        msg['To']      = destinatario

        msg.attach(MIMEText(texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(html,  'html',  'utf-8'))

        print(f"[EMAIL] Conectando a {server_host}:{server_port} para {destinatario}...")
        
        if server_port == 465:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=15)
        else:
            server = smtplib.SMTP(server_host, server_port, timeout=15)
            server.starttls()
            
        server.login(username, password)
        # CRÍTICO: send_message maneja automáticamente codificación UTF-8 (ñ, tildes)
        server.send_message(msg)
        server.quit()

        print(f"[EMAIL] ✅ Éxito al enviar a {destinatario}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] ❌ Falló el envío: {e}")
        return False

def enviar_correo_verificacion(usuario, token: str) -> bool:
    from flask import url_for, current_app
    enlace = url_for('auth.verificar', token=token, _external=True)
    
    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando verificación para {usuario.email}")
    
    if not _smtp_configurado():
        print(f"DEBUG: Enlace -> {enlace}")
        return True

    asunto = '✅ Confirma tu cuenta en U-Ride'
    
    # HTML Simplificado idéntico a test_email.py
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
      <div style="background:#dc2626;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🚗 U-Ride</h1>
      </div>
      <div style="padding:24px;background:#ffffff;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
        <h2 style="color:#111827;">¡Verifica tu cuenta!</h2>
        <p style="color:#6b7280;">
          Hola {usuario.nombre},<br><br>
          Gracias por registrarte. Por favor, confirma tu correo institucional haciendo clic en el siguiente enlace:
        </p>
        <p style="margin:30px 0;text-align:center;">
          <a href="{enlace}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;">Verificar Cuenta</a>
        </p>
        <p style="color:#6b7280;font-size:12px;">
          Si el botón no funciona, ingresa a esta URL:<br>{enlace}
        </p>
      </div>
    </div>
    """
    
    texto = f"Hola {usuario.nombre}, verifica tu cuenta aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)

def enviar_correo_recuperacion(usuario, token: str) -> bool:
    from flask import url_for, current_app
    enlace = url_for('auth.reset_password', token=token, _external=True)

    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando recuperación para {usuario.email}")

    if not _smtp_configurado():
        print(f"DEBUG: Enlace -> {enlace}")
        return True

    asunto = '🔒 Restablece tu contraseña en U-Ride'
    
    # HTML Simplificado idéntico a test_email.py
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
      <div style="background:#dc2626;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🚗 U-Ride</h1>
      </div>
      <div style="padding:24px;background:#ffffff;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
        <h2 style="color:#111827;">Recuperación de contraseña</h2>
        <p style="color:#6b7280;">
          Hola {usuario.nombre},<br><br>
          Hemos recibido una solicitud para cambiar tu contraseña. Haz clic en el enlace de abajo para continuar:
        </p>
        <p style="margin:30px 0;text-align:center;">
          <a href="{enlace}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;">Cambiar Contraseña</a>
        </p>
        <p style="color:#6b7280;font-size:12px;">
          Si el botón no funciona, ingresa a esta URL:<br>{enlace}
        </p>
      </div>
    </div>
    """
    
    texto = f"Hola {usuario.nombre}, cambia tu contraseña aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)
