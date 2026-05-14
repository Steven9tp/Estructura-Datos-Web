"""
Utilidades de autenticacion para U-Ride
=========================================
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
    enlace = url_for('auth.verificar', token=token, _external=True)
    
    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando verificación para {usuario.email}")

    asunto = '✅ Confirma tu cuenta en U-Ride'
    
    # HTML Simplificado y optimizado
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
    
    return _enviar_http(usuario.email, asunto, html)

def enviar_correo_recuperacion(usuario, token: str) -> bool:
    from flask import url_for, current_app
    enlace = url_for('auth.reset_password', token=token, _external=True)

    # Forzar HTTPS si estamos en producción (Render)
    if 'onrender.com' in enlace or current_app.config.get('PREFERRED_URL_SCHEME') == 'https':
        enlace = enlace.replace('http://', 'https://')

    print(f"\n[EMAIL] Preparando recuperación para {usuario.email}")

    asunto = '🔒 Restablece tu contraseña en U-Ride'
    
    # HTML Simplificado
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

    return _enviar_http(usuario.email, asunto, html)
