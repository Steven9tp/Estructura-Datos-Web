"""
Utilidades de autenticacion para U-Ride
=========================================
Envia emails usando smtplib directamente (igual que test_email.py).
Configura en .env: MAIL_USERNAME, MAIL_PASSWORD (contrasena de app de Google).
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _smtp_configurado() -> bool:
    """Retorna True si las credenciales SMTP estan configuradas y son validas."""
    username = os.getenv('MAIL_USERNAME', '').strip()
    password = os.getenv('MAIL_PASSWORD', '').strip()

    if not username or not password:
        return False

    placeholders = ('TU_CORREO_REAL', 'tu_correo', 'your_email', 'example',
                    'CONTRASENA', 'TU_CONTRASENA', 'your_password')
    if any(p.lower() in username.lower() for p in placeholders):
        return False
    if any(p.lower() in password.lower() for p in placeholders):
        return False
    if len(password) < 16:
        return False

    return True


def _enviar_smtp(destinatario: str, asunto: str, html: str, texto: str) -> bool:
    """Envia email via SMTP — identico a test_email.py para maxima compatibilidad."""
    server_host = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    server_port = int(os.getenv('MAIL_PORT', 587))
    username    = os.getenv('MAIL_USERNAME', '').strip()
    password    = os.getenv('MAIL_PASSWORD', '').strip()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From']    = f'U-Ride <{username}>'
        msg['To']      = destinatario

        msg.attach(MIMEText(texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(html,  'html',  'utf-8'))

        # Conexion identica a test_email.py
        server = smtplib.SMTP(server_host, server_port, timeout=15)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, [destinatario], msg.as_string())
        server.quit()

        logger.info(f'[EMAIL] Enviado a {destinatario}: {asunto}')
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f'[EMAIL] Error de autenticacion: {e}')
        print(f'[EMAIL ERROR] Autenticacion fallida: {e}')
        return False
    except Exception as e:
        logger.error(f'[EMAIL] Error enviando a {destinatario}: {e}')
        print(f'[EMAIL ERROR] {type(e).__name__}: {e}')
        return False


def verificar_dominio_institucional(email: str) -> bool:
    """Verifica que el email pertenezca al dominio institucional (@uta.edu.ec)."""
    dominio = os.getenv('DOMINIO_INSTITUCIONAL', '@uta.edu.ec')
    return email.strip().lower().endswith(dominio.lower())


# ─────────────────────────────────────────────────────────────────────────────
# Templates de email — simples para evitar filtros de spam
# ─────────────────────────────────────────────────────────────────────────────

def _html_verificacion(nombre: str, enlace: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
      <div style="background:#dc2626;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;font-size:22px;">U-Ride</h1>
        <p style="color:#fecaca;margin:4px 0 0;font-size:13px;">Universidad Tecnica de Ambato</p>
      </div>
      <div style="padding:28px 32px;background:#ffffff;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
        <h2 style="color:#111827;margin:0 0 12px;">Verifica tu cuenta</h2>
        <p style="color:#374151;margin:0 0 8px;">Hola <strong>{nombre}</strong>,</p>
        <p style="color:#6b7280;margin:0 0 24px;">
          Gracias por unirte a U-Ride. Haz clic en el boton para activar tu cuenta.
        </p>
        <a href="{enlace}"
           style="display:inline-block;background:#dc2626;color:#ffffff;
                  text-decoration:none;padding:12px 28px;border-radius:6px;
                  font-weight:bold;font-size:15px;">
          Verificar mi cuenta
        </a>
        <p style="color:#9ca3af;font-size:12px;margin:24px 0 0;">
          Si el boton no funciona, copia este enlace:<br>
          <a href="{enlace}" style="color:#dc2626;word-break:break-all;">{enlace}</a>
        </p>
        <hr style="border:none;border-top:1px solid #f3f4f6;margin:20px 0;">
        <p style="color:#9ca3af;font-size:11px;margin:0;">
          Enlace valido 24 horas. Si no creaste esta cuenta, ignora este mensaje.
        </p>
      </div>
    </div>
    """


def _html_recuperacion(nombre: str, enlace: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
      <div style="background:#dc2626;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;font-size:22px;">U-Ride</h1>
        <p style="color:#fecaca;margin:4px 0 0;font-size:13px;">Universidad Tecnica de Ambato</p>
      </div>
      <div style="padding:28px 32px;background:#ffffff;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
        <h2 style="color:#111827;margin:0 0 12px;">Restablece tu contrasena</h2>
        <p style="color:#374151;margin:0 0 8px;">Hola <strong>{nombre}</strong>,</p>
        <p style="color:#6b7280;margin:0 0 24px;">
          Recibimos una solicitud para cambiar la contrasena de tu cuenta en U-Ride.
          Si no lo solicitaste, ignora este mensaje.
        </p>
        <a href="{enlace}"
           style="display:inline-block;background:#dc2626;color:#ffffff;
                  text-decoration:none;padding:12px 28px;border-radius:6px;
                  font-weight:bold;font-size:15px;">
          Cambiar contrasena
        </a>
        <p style="color:#9ca3af;font-size:12px;margin:24px 0 0;">
          Si el boton no funciona, copia este enlace:<br>
          <a href="{enlace}" style="color:#dc2626;word-break:break-all;">{enlace}</a>
        </p>
        <hr style="border:none;border-top:1px solid #f3f4f6;margin:20px 0;">
        <p style="color:#9ca3af;font-size:11px;margin:0;">
          Enlace valido 1 hora. Tu contrasena actual no ha sido modificada.
        </p>
      </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Funciones publicas
# ─────────────────────────────────────────────────────────────────────────────

def enviar_correo_verificacion(usuario, token: str) -> bool:
    """Envia correo de verificacion de cuenta (SMTP real o consola DEV)."""
    from flask import url_for
    enlace = url_for('auth.verificar', token=token, _external=True)

    # Siempre imprimir en consola como respaldo
    print()
    print('=' * 65)
    print('  [U-Ride] VERIFICACION DE CUENTA')
    print(f'  Usuario : {usuario.nombre} <{usuario.email}>')
    print(f'  Enlace  : {enlace}')
    print('  Validez : 24 horas')
    print('=' * 65)

    if not _smtp_configurado():
        print('  MODO DEV: sin SMTP. Usa el enlace de arriba.')
        print()
        return True

    asunto = 'Confirma tu cuenta en U-Ride'
    html   = _html_verificacion(usuario.nombre, enlace)
    texto  = (
        f'Hola {usuario.nombre},\n\n'
        f'Confirma tu cuenta en U-Ride:\n{enlace}\n\n'
        f'Valido 24 horas. Si no creaste esta cuenta, ignora este mensaje.\n\n'
        f'U-Ride - Universidad Tecnica de Ambato'
    )

    resultado = _enviar_smtp(usuario.email, asunto, html, texto)
    if resultado:
        print(f'  >> Correo enviado por SMTP a {usuario.email}')
    else:
        print(f'  >> SMTP fallo. Usa el enlace de arriba para verificar.')
    print()
    return resultado


def enviar_correo_recuperacion(usuario, token: str) -> bool:
    """Envia correo de recuperacion de contrasena (SMTP real o consola DEV)."""
    from flask import url_for
    enlace = url_for('auth.reset_password', token=token, _external=True)

    # Siempre imprimir en consola como respaldo
    print()
    print('=' * 65)
    print('  [U-Ride] RECUPERACION DE CONTRASENA')
    print(f'  Usuario : {usuario.nombre} <{usuario.email}>')
    print(f'  Enlace  : {enlace}')
    print('  Validez : 1 hora')
    print('=' * 65)

    if not _smtp_configurado():
        print('  MODO DEV: sin SMTP. Usa el enlace de arriba.')
        print()
        return True

    asunto = 'Restablece tu contrasena en U-Ride'
    html   = _html_recuperacion(usuario.nombre, enlace)
    texto  = (
        f'Hola {usuario.nombre},\n\n'
        f'Restablece tu contrasena en U-Ride:\n{enlace}\n\n'
        f'Expira en 1 hora. Si no lo solicitaste, ignora este mensaje.\n\n'
        f'U-Ride - Universidad Tecnica de Ambato'
    )

    resultado = _enviar_smtp(usuario.email, asunto, html, texto)
    if resultado:
        print(f'  >> Correo enviado por SMTP a {usuario.email}')
    else:
        print(f'  >> SMTP fallo. Usa el enlace de arriba para recuperar.')
    print()
    return resultado


def enviar_recordatorio_calificacion(conductor, pasajero, viaje) -> bool:
    """Envia recordatorio de calificacion tras un viaje finalizado."""
    if not _smtp_configurado():
        return True

    asunto = 'Califica tu experiencia en U-Ride'
    html   = f'<p>Hola {pasajero.nombre}, califica tu viaje con {conductor.nombre}.</p>'
    texto  = f'Hola {pasajero.nombre}, califica tu viaje con {conductor.nombre} en U-Ride.'

    return _enviar_smtp(pasajero.email, asunto, html, texto)
