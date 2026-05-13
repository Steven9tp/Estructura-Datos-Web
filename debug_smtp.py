import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

def test_smtp():
    server_host = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    server_port = int(os.getenv('MAIL_PORT', 587))
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')

    print(f"--- TEST SMTP ---")
    print(f"Server: {server_host}")
    print(f"Port: {server_port}")
    print(f"User: {username}")
    print(f"Pass: {'*' * len(password) if password else 'None'}")
    print("------------------")

    if not username or not password:
        print("Error: MAIL_USERNAME o MAIL_PASSWORD no están configurados.")
        return

    try:
        print("Conectando al servidor...")
        if server_port == 465:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=15)
        else:
            server = smtplib.SMTP(server_host, server_port, timeout=15)
            server.starttls()
        
        print("Intentando login...")
        server.login(username, password)
        
        print("Enviando correo de prueba...")
        msg = MIMEText("Prueba de conexión desde script de diagnóstico.")
        msg['Subject'] = "Test U-Ride"
        msg['From'] = username
        msg['To'] = username
        
        server.sendmail(username, [username], msg.as_string())
        server.quit()
        print("✅ ÉXITO: El correo fue enviado correctamente.")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ ERROR: Autenticación fallida. Verifica que la 'Contraseña de Aplicación' sea correcta y no tenga espacios.")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_smtp()
