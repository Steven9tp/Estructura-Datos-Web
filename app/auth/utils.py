"""
Utilidades de autenticación para SmartCampus UTA
=================================================
Usa la API HTTP de Google Apps Script para evitar el bloqueo del puerto SMTP (25, 465, 587) de Render.
"""
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwnd4Oaqby2NCP6JRHMMyzy0MWCXuTyMck4kHFECvQGC6-CC2URT5vePh9-pixUs9C/exec"

def _enviar_http(destinatario: str, asunto: str, html: str) -> bool:
    """Envía el correo usando la API HTTP para esquivar los bloqueos de Render."""
    data = {
        "to": destinatario,
        "subject": asunto,
        "html": html
    }
    
    print(f"[EMAIL API] Contactando con Google Apps Script para enviar a {destinatario}...")
    
    try:
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            GOOGLE_SCRIPT_URL, 
            data=payload, 
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result_text = response.read().decode('utf-8')
            try:
                result = json.loads(result_text)
                if result.get('status') == 'success':
                    print(f"[EMAIL API] ✅ Éxito al enviar a {destinatario}")
                    return True
                else:
                    print(f"[EMAIL API ERROR] ❌ Google Script devolvió error: {result}")
                    return False
            except json.JSONDecodeError:
                print(f"[EMAIL API ERROR] ❌ Respuesta no es JSON válida: {result_text}")
                return False

    except Exception as e:
        print(f"[EMAIL API ERROR] ❌ Falló la conexión HTTP: {e}")
        return False

def enviar_correo_verificacion(usuario, token: str) -> bool:
    from flask import url_for, current_app
    enlace = url_for('auth.verificar_email', token=token, _external=True)
    
    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando verificación para {usuario.email}")

    asunto = '✅ Confirma tu cuenta en SmartCampus UTA'
    
    # HTML elegante para SmartCampus con temática dorado/carbón
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; background-color: #f9fafb; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb;">
      <div style="background: #111827; padding: 30px; text-align: center; border-bottom: 3px solid #d97706;">
        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;">🏛️ SmartCampus UTA</h1>
      </div>
      <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 0; margin-bottom: 16px;">¡Hola {usuario.nombres}!</h2>
        <p style="color: #4b5563; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
          Gracias por registrarte en nuestra plataforma académica. Para completar tu registro y activar tu cuenta institucional, haz clic en el siguiente botón:
        </p>
        <div style="margin: 35px 0; text-align: center;">
          <a href="{enlace}" style="background: #d97706; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.2);">Activar Mi Cuenta</a>
        </div>
        <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin-bottom: 8px;">
          Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:
        </p>
        <p style="color: #d97706; font-size: 13px; word-break: break-all; margin: 0 0 24px 0; font-family: monospace;">
          {enlace}
        </p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">
          Este es un correo automático, por favor no respondas a este mensaje.
        </p>
      </div>
    </div>
    """
    
    return _enviar_http(usuario.email, asunto, html)

def enviar_correo_recuperacion(usuario, token: str) -> bool:
    from flask import url_for, current_app
    enlace = url_for('auth.reset_password', token=token, _external=True)

    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando recuperación para {usuario.email}")

    asunto = '🔒 Restablece tu contraseña - SmartCampus UTA'
    
    # HTML elegante para SmartCampus con temática dorado/carbón
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; background-color: #f9fafb; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb;">
      <div style="background: #111827; padding: 30px; text-align: center; border-bottom: 3px solid #d97706;">
        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;">🏛️ SmartCampus UTA</h1>
      </div>
      <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 0; margin-bottom: 16px;">Restablecer Contraseña</h2>
        <p style="color: #4b5563; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
          Hemos recibido una solicitud para restablecer la contraseña de tu cuenta académica. Si fuiste tú, haz clic en el siguiente botón para crear una nueva contraseña:
        </p>
        <div style="margin: 35px 0; text-align: center;">
          <a href="{enlace}" style="background: #d97706; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.2);">Restablecer Contraseña</a>
        </div>
        <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin-bottom: 8px;">
          Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:
        </p>
        <p style="color: #d97706; font-size: 13px; word-break: break-all; margin: 0 0 24px 0; font-family: monospace;">
          {enlace}
        </p>
        <p style="color: #6b7280; font-size: 14px; line-height: 1.5;">
          Si no solicitaste este cambio, puedes ignorar este correo de forma segura. Tu contraseña actual no cambiará.
        </p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">
          Este es un correo automático, por favor no respondas a este mensaje.
        </p>
      </div>
    </div>
    """

    return _enviar_http(usuario.email, asunto, html)
