r"""
Script de diagnóstico de SMTP para U-Ride.
Ejecutar: venv/Scripts/python test_email.py tu_correo@uta.edu.ec
"""
import sys
import os

# Cargar .env manualmente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env cargado")
except ImportError:
    print("⚠️  python-dotenv no instalado, leyendo variables del sistema")

# Leer configuración
MAIL_SERVER   = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT     = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

print()
print("=" * 55)
print("  DIAGNÓSTICO DE EMAIL — U-Ride")
print("=" * 55)
print(f"  Servidor : {MAIL_SERVER}:{MAIL_PORT}")
print(f"  Usuario  : {MAIL_USERNAME}")
print(f"  Password : {'*' * len(MAIL_PASSWORD)} ({len(MAIL_PASSWORD)} chars)")
print("=" * 55)

# Destinatario desde argumento o interactivo
if len(sys.argv) > 1:
    destinatario = sys.argv[1]
else:
    destinatario = input("\n¿A qué correo enviar la prueba? → ").strip()

if not destinatario:
    print("❌ No se ingresó destinatario. Abortando.")
    sys.exit(1)

print(f"\n📧 Enviando correo de prueba a: {destinatario}")
print("   Conectando con Gmail SMTP...\n")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    # Conectar al servidor SMTP
    print(f"  [1/4] Conectando a {MAIL_SERVER}:{MAIL_PORT} ...")
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15)
    print("  ✅ Conexión establecida")

    print("  [2/4] Iniciando STARTTLS ...")
    server.starttls()
    print("  ✅ TLS activo")

    print(f"  [3/4] Autenticando como {MAIL_USERNAME} ...")
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    print("  ✅ Autenticación exitosa")

    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '✅ Prueba de correo — U-Ride'
    msg['From']    = f'U-Ride <{MAIL_USERNAME}>'
    msg['To']      = destinatario

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
      <div style="background:#dc2626;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🚗 U-Ride</h1>
      </div>
      <div style="padding:24px;background:#ffffff;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
        <h2 style="color:#111827;">¡Correo de prueba exitoso!</h2>
        <p style="color:#6b7280;">
          Si ves este mensaje, el sistema de envío de correos de U-Ride
          está funcionando correctamente.
        </p>
        <p style="color:#6b7280;">
          Enviado desde: <strong>{MAIL_USERNAME}</strong><br>
          Destinatario : <strong>{destinatario}</strong>
        </p>
      </div>
    </div>
    """
    texto = f"Prueba de correo U-Ride\n\nSi ves este mensaje, el SMTP funciona.\nEnviado desde: {MAIL_USERNAME}"

    msg.attach(MIMEText(texto, 'plain', 'utf-8'))
    msg.attach(MIMEText(html,  'html',  'utf-8'))

    print(f"  [4/4] Enviando a {destinatario} ...")
    server.sendmail(MAIL_USERNAME, [destinatario], msg.as_string())
    server.quit()

    print()
    print("=" * 55)
    print("  ✅ ¡CORREO ENVIADO EXITOSAMENTE!")
    print(f"  Revisa la bandeja de entrada de: {destinatario}")
    print("  (también revisa SPAM si no aparece)")
    print("=" * 55)

except smtplib.SMTPAuthenticationError as e:
    print()
    print("=" * 55)
    print("  ❌ ERROR DE AUTENTICACIÓN")
    print(f"  {e}")
    print()
    print("  Posibles causas:")
    print("  1. La contraseña de app es incorrecta en .env")
    print("  2. La verificación en 2 pasos no está activa")
    print("  3. La contraseña tiene caracteres incorrectos")
    print()
    print("  Solución: Genera una nueva contraseña de app en:")
    print("  https://myaccount.google.com/apppasswords")
    print("=" * 55)

except smtplib.SMTPConnectError as e:
    print()
    print("  ❌ ERROR DE CONEXIÓN")
    print(f"  {e}")
    print("  Verifica tu conexión a internet y que el puerto 587 no esté bloqueado.")

except Exception as e:
    print()
    print("=" * 55)
    print(f"  ❌ ERROR: {type(e).__name__}")
    print(f"  {e}")
    print("=" * 55)
