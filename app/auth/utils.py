"""
Utilidades de autenticacion para U-Ride
=========================================
Usa smtplib directamente (igual que test_email.py que SI funciona).
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
    """Lógica exacta de test_email.py para máxima compatibilidad."""
    server_host = os.getenv('MAIL_SERVER', 'smtp.gmail.com').strip()
    server_port = int(os.getenv('MAIL_PORT', 587))
    username    = os.getenv('MAIL_USERNAME', '').strip()
    password    = os.getenv('MAIL_PASSWORD', '').strip()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From']    = f"U-Ride <{username}>"
        msg['To']      = destinatario

        msg.attach(MIMEText(texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(html,  'html',  'utf-8'))

        print(f"[EMAIL] Conectando a {server_host}:{server_port}...")
        
        # Soportar explícitamente ambos puertos (Render recomienda 465)
        if server_port == 465:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=15)
        else:
            server = smtplib.SMTP(server_host, server_port, timeout=15)
            server.starttls()
            
        server.login(username, password)
        server.sendmail(username, [destinatario], msg.as_string())
        server.quit()

        print(f"[EMAIL] Éxito al enviar a {destinatario}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Falló el envío: {e}")
        return False

def enviar_correo_verificacion(usuario, token: str) -> bool:
    from flask import url_for
    enlace = url_for('auth.verificar', token=token, _external=True)

    print(f"\n[EMAIL] Preparando verificación para {usuario.email}")
    
    if not _smtp_configurado():
        print(f"DEBUG: Enlace -> {enlace}")
        return True

    asunto = '🚗 Confirma tu cuenta en U-Ride'
    
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <div style="background:#dc2626;padding:20px;text-align:center;">
        <h1 style="color:white;margin:0;">🚗 U-Ride</h1>
      </div>
      <div style="padding:24px;background:#ffffff;">
        <h2 style="color:#111827;margin-top:0;">Hola, {usuario.nombre}!</h2>
        <p style="color:#4b5563;font-size:16px;">
          Gracias por registrarte en U-Ride. Para completar tu registro y poder iniciar sesión, necesitamos verificar tu correo institucional.
        </p>
        <div style="text-align:center;margin:30px 0;">
          <a href="{enlace}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">Verificar mi cuenta</a>
        </div>
        <p style="color:#6b7280;font-size:14px;margin-bottom:0;">
          Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
          <span style="color:#dc2626;word-break:break-all;">{enlace}</span>
        </p>
      </div>
    </div>
    """
    
    texto = f"Hola {usuario.nombre}, verifica tu cuenta aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)

def enviar_correo_recuperacion(usuario, token: str) -> bool:
    from flask import url_for
    enlace = url_for('auth.reset_password', token=token, _external=True)

    print(f"\n[EMAIL] Preparando recuperación para {usuario.email}")

    if not _smtp_configurado():
        print(f"DEBUG: Enlace -> {enlace}")
        return True

    asunto = '🚗 Restablece tu contraseña en U-Ride'
    
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <div style="background:#dc2626;padding:20px;text-align:center;">
        <h1 style="color:white;margin:0;">🚗 U-Ride</h1>
      </div>
      <div style="padding:24px;background:#ffffff;">
        <h2 style="color:#111827;margin-top:0;">Hola, {usuario.nombre}!</h2>
        <p style="color:#4b5563;font-size:16px;">
          Hemos recibido una solicitud para cambiar tu contraseña en U-Ride.
        </p>
        <div style="text-align:center;margin:30px 0;">
          <a href="{enlace}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">Cambiar mi contraseña</a>
        </div>
        <p style="color:#6b7280;font-size:14px;margin-bottom:0;">
          Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
          <span style="color:#dc2626;word-break:break-all;">{enlace}</span>
        </p>
      </div>
    </div>
    """
    
    texto = f"Hola {usuario.nombre}, cambia tu contraseña aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)
