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
    server_port = int(os.getenv('MAIL_PORT', 465))
    username    = os.getenv('MAIL_USERNAME', '').strip()
    password    = os.getenv('MAIL_PASSWORD', '').strip()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From']    = f"U-Ride <{username}>"
        msg['To']      = destinatario

        msg.attach(MIMEText(texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(html,  'html',  'utf-8'))

        # Usar SSL directo (puerto 465) o TLS (587)
        if server_port == 465:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=20)
        else:
            server = smtplib.SMTP(server_host, server_port, timeout=20)
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

    asunto = 'Confirma tu cuenta en U-Ride'
    html = f"<h2>Hola {usuario.nombre}</h2><p>Verifica tu cuenta aquí: <a href='{enlace}'>{enlace}</a></p>"
    texto = f"Hola {usuario.nombre}, verifica tu cuenta aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)

def enviar_correo_recuperacion(usuario, token: str) -> bool:
    from flask import url_for
    enlace = url_for('auth.reset_password', token=token, _external=True)

    print(f"\n[EMAIL] Preparando recuperación para {usuario.email}")

    if not _smtp_configurado():
        print(f"DEBUG: Enlace -> {enlace}")
        return True

    asunto = 'Restablece tu contraseña en U-Ride'
    html = f"<h2>Hola {usuario.nombre}</h2><p>Cambia tu contraseña aquí: <a href='{enlace}'>{enlace}</a></p>"
    texto = f"Hola {usuario.nombre}, cambia tu contraseña aquí: {enlace}"

    return _enviar_smtp(usuario.email, asunto, html, texto)
