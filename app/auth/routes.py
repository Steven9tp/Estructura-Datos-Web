"""
Rutas de autenticación para U-Ride

Flujo de registro:
    POST /auth/registro → crea usuario (email_verificado=False)
                        → imprime token en consola (modo DEV)
                        → redirige a /auth/verificar-enviado

Flujo de verificación:
    GET /auth/verificar/<token> → valida token firmado (24h)
                                → marca email_verificado=True
                                → redirige al login

Flujo de recuperación:
    POST /auth/recuperar        → genera token (1h) e imprime enlace en consola
    GET/POST /auth/reset-password/<token> → valida token → cambia password

Nota DEV: sin SMTP configurado los enlaces se imprimen en la consola del servidor.
"""
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

from app import db
from app.auth import bp
from app.forms import LoginForm, RegistroForm, RecuperarPasswordForm, ResetPasswordForm
from app.models import Usuario
from app.auth.utils import (
    enviar_correo_verificacion,
    enviar_correo_recuperacion
)


# ─────────────────────────────────────────────────────────────────────────────
# Login / Logout
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Inicia sesión.
    Requisitos para acceder:
     - cuenta existente con correo @uta.edu.ec
     - email_verificado = True
     - esta_activo = True
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        # Contraseña incorrecta o usuario no existe
        if usuario is None or not usuario.check_password(form.password.data):
            flash('Correo o contraseña inválidos.', 'danger')
            return redirect(url_for('auth.login'))

        # Cuenta suspendida
        if not usuario.esta_activo:
            flash('Tu cuenta está suspendida. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.login'))

        # Email no verificado — ofrece reenviar enlace
        if not usuario.email_verificado:
            flash(
                Markup(
                    'Debes verificar tu correo antes de iniciar sesión. '
                    '¿No recibiste el enlace? '
                    f'<a href="{url_for("auth.reenviar_verificacion")}">Reenviar verificación</a>'
                ),
                'warning'
            )
            return redirect(url_for('auth.login'))

        login_user(usuario, remember=form.remember_me.data)
        flash(f'¡Bienvenido de nuevo, {usuario.nombre}!', 'success')

        # Protección contra Open Redirect
        next_page = request.args.get('next')
        if next_page and urlparse(next_page).netloc == '' and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', title='Iniciar Sesión', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('main.index'))


# ─────────────────────────────────────────────────────────────────────────────
# Registro
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    Registra un nuevo usuario.

    La validación del dominio institucional se realiza en RegistroForm.validate_email().
    Después del registro exitoso el usuario recibe un email (o token en consola)
    y debe verificar su cuenta antes de iniciar sesión.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistroForm()
    if form.validate_on_submit():
        # El form ya validó: dominio correcto + email no duplicado
        usuario = Usuario(
            nombre=form.nombre.data.strip(),
            apellido=form.apellido.data.strip(),
            email=form.email.data.strip().lower(),
            carrera=form.carrera.data.strip() if form.carrera.data else '',
            zona_barrio=form.zona_barrio.data,
            telefono=form.telefono.data.strip() if form.telefono.data else '',
            email_verificado=False,  # Debe verificar por correo
            esta_activo=True,
            es_admin=False
        )
        usuario.set_password(form.password.data)

        try:
            db.session.add(usuario)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error al registrar usuario: {e}')
            flash('Ocurrió un error al crear la cuenta. Intenta de nuevo.', 'danger')
            return render_template('auth/registro.html', title='Registro', form=form)

        # Generar y enviar token de verificación
        token = usuario.generar_token_verificacion()
        enviado = enviar_correo_verificacion(usuario, token)

        if enviado:
            flash(
                '¡Registro exitoso! Revisa tu correo institucional para verificar tu cuenta.',
                'success'
            )
        else:
            flash(
                '¡Registro exitoso! Hubo un problema al enviar el correo. '
                'Contacta al administrador.',
                'warning'
            )

        return redirect(url_for('auth.verificar_enviado'))

    return render_template('auth/registro.html', title='Registro', form=form)


# ─────────────────────────────────────────────────────────────────────────────
# Verificación de correo
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/verificar-enviado')
def verificar_enviado():
    """Página informativa después de enviar el correo de verificación."""
    return render_template('auth/verificar.html', title='Verifica tu Correo')


@bp.route('/verificar/<token>')
def verificar(token):
    """
    Verifica el correo del usuario mediante el token firmado.

    El token es válido por 24 horas.
    Si el token es inválido o expiró, redirige al login con mensaje de error.
    """
    # Verificar token (24h de validez)
    email = Usuario.verificar_token(token, salt='verificar-email', max_age=86400)

    if email is None:
        flash(
            Markup(
                'El enlace de verificación es inválido o ha expirado (válido 24h). '
                f'<a href="{url_for("auth.reenviar_verificacion")}">Solicitar nuevo enlace</a>'
            ),
            'danger'
        )
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None:
        flash('No se encontró la cuenta asociada a este enlace.', 'danger')
        return redirect(url_for('auth.login'))

    if usuario.email_verificado:
        flash('Tu cuenta ya estaba verificada. Puedes iniciar sesión.', 'info')
        return redirect(url_for('auth.login'))

    usuario.email_verificado = True
    db.session.commit()
    flash('✅ ¡Tu cuenta ha sido verificada! Ya puedes iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/reenviar-verificacion', methods=['GET', 'POST'])
def reenviar_verificacion():
    """
    Permite al usuario solicitar un nuevo correo de verificación.
    El mensaje de respuesta es genérico para no revelar si el correo existe.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        # Enviar solo si existe y no está verificado
        if usuario and not usuario.email_verificado:
            token = usuario.generar_token_verificacion()
            enviar_correo_verificacion(usuario, token)

        # Mensaje genérico para no revelar info de la BD
        flash(
            'Si el correo existe y no está verificado, recibirás un nuevo enlace.',
            'info'
        )
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/reenviar_verificacion.html',
        title='Reenviar Verificación'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Recuperación de contraseña
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar_password():
    """
    Paso 1 — Solicitar recuperación de contraseña.

    El form valida que sea un correo @uta.edu.ec.
    El mensaje de respuesta es genérico para no revelar si el correo existe.
    Token válido por 1 hora.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RecuperarPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            if usuario.email_verificado:
                # Cuenta verificada → enviar enlace de recuperación
                token = usuario.generar_token_recuperacion()
                enviar_correo_recuperacion(usuario, token)
                flash(
                    'Te enviamos un correo con instrucciones para restablecer tu contraseña.',
                    'info'
                )
            else:
                # Cuenta sin verificar → reenviar verificación primero
                token = usuario.generar_token_verificacion()
                enviar_correo_verificacion(usuario, token)
                flash(
                    'Tu cuenta aún no está verificada. '
                    'Te reenviamos el correo de verificación — revisa tu bandeja.',
                    'warning'
                )
        else:
            # No revelar si el correo existe o no
            flash(
                'Si tu cuenta existe, recibirás un correo con instrucciones.',
                'info'
            )

        return redirect(url_for('auth.login'))

    return render_template('auth/recuperar.html', title='Recuperar Contraseña', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Paso 2 — Restablecer contraseña con token.

    El token es válido por 1 hora (3600 segundos).
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Verificar token (1h de validez)
    email = Usuario.verificar_token(token, salt='recuperar-password', max_age=3600)

    if email is None:
        flash(
            'El enlace de recuperación es inválido o ha expirado (válido 1h). '
            'Solicita uno nuevo.',
            'danger'
        )
        return redirect(url_for('auth.recuperar_password'))

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None:
        flash('No se encontró la cuenta asociada a este enlace.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        usuario.set_password(form.password.data)
        db.session.commit()
        flash('✅ ¡Contraseña restablecida! Ya puedes iniciar sesión con tu nueva contraseña.', 'success')
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/reset_password.html',
        title='Nueva Contraseña',
        form=form
    )


# ─────────────────────────────────────────────────────────────────────────────
# Diagnóstico SMTP (solo desarrollo — eliminar en producción)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/debug-verificacion')
def debug_verificacion():
    """
    Muestra en consola los enlaces de verificación para cuentas no verificadas.
    Uso: http://127.0.0.1:5000/auth/debug-verificacion
    """
    from flask import jsonify
    no_verificados = Usuario.query.filter_by(email_verificado=False).all()
    enlaces = []
    for u in no_verificados:
        token  = u.generar_token_verificacion()
        enlace = url_for('auth.verificar', token=token, _external=True)
        enlaces.append({'email': u.email, 'nombre': u.nombre, 'enlace': enlace})
        print(f'  [DEBUG] Verificar {u.email}: {enlace}')
    return jsonify({'usuarios_sin_verificar': len(no_verificados), 'enlaces': enlaces})


@bp.route('/test-email/<destinatario>')
def test_email_route(destinatario):
    """
    Endpoint de diagnóstico: prueba el envío de email desde el contexto Flask.
    Uso: http://127.0.0.1:5000/auth/test-email/tu_correo@ejemplo.com
    """
    import os
    import smtplib
    from flask import jsonify

    username = os.getenv('MAIL_USERNAME', '').strip()
    password = os.getenv('MAIL_PASSWORD', '').strip()
    server   = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    port     = int(os.getenv('MAIL_PORT', 587))

    resultado = {
        'MAIL_SERVER':   server,
        'MAIL_PORT':     port,
        'MAIL_USERNAME': username,
        'MAIL_PASSWORD': '*' * len(password) + f' ({len(password)} chars)',
        'smtp_configurado': None,
        'envio_exitoso': None,
        'error': None
    }

    # Verificar si está configurado
    if not username or len(password) < 16:
        resultado['smtp_configurado'] = False
        resultado['error'] = 'Credenciales no configuradas o password < 16 chars'
        return jsonify(resultado)

    resultado['smtp_configurado'] = True

    # Intentar enviar
    try:
        from email.mime.text import MIMEText
        msg = MIMEText(f'Prueba desde Flask. Destinatario: {destinatario}', 'plain', 'utf-8')
        msg['Subject'] = '🔧 Test SMTP desde Flask — U-Ride'
        msg['From']    = username
        msg['To']      = destinatario

        smtp = smtplib.SMTP(server, port, timeout=15)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)   # send_message maneja UTF-8 correctamente
        smtp.quit()

        resultado['envio_exitoso'] = True
    except Exception as e:
        resultado['envio_exitoso'] = False
        resultado['error'] = f'{type(e).__name__}: {str(e)}'

    return jsonify(resultado)