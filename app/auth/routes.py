from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from app import db, mail
from flask_mail import Message
from app.auth import bp
from app.forms import LoginForm, RegistroForm, OlvidePasswordForm, ResetPasswordForm
from app.models import Usuario

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Correo o contraseña inválidos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not getattr(user, 'email_verificado', True) and user.tipo_usuario != 'admin':
            flash('Por favor verifica tu correo institucional antes de iniciar sesión. Revisa tu bandeja de entrada o spam.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistroForm()
    if form.validate_on_submit():
        user = Usuario(
            nombres=form.nombres.data,
            apellidos=form.apellidos.data,
            cedula=form.cedula.data,
            email=form.email.data,
            tipo_usuario=form.tipo_usuario.data,
            email_verificado=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        token = user.get_token()
        msg = Message('Verifica tu correo institucional - SmartCampus UTA',
                      sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@smartcampus.com'),
                      recipients=[user.email])
        link = url_for('auth.verificar_email', token=token, _external=True)
        msg.body = f'''¡Hola {user.nombres}! Gracias por registrarte en SmartCampus UTA.
Para completar tu registro y activar tu cuenta, haz clic en el siguiente enlace:
{link}

Si tú no solicitaste este registro, ignora este correo.
'''
        try:
            mail.send(msg)
            flash('¡Te has registrado con éxito! Te hemos enviado un correo institucional para verificar tu cuenta.', 'success')
        except Exception as e:
            print("Error enviando correo:", e)
            print(f"ENLACE DE VERIFICACION (FALLBACK): {link}")
            flash('Registro exitoso. El servidor de correo de Render está bloqueado, pero tu enlace se imprimió en los logs.', 'warning')

        return redirect(url_for('auth.login'))
    return render_template('auth/registro.html', title='Registro', form=form)

@bp.route('/verificar_email/<token>')
def verificar_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = Usuario.verify_token(token)
    if not user:
        flash('El enlace de verificación es inválido o ha expirado. Por favor, regístrate de nuevo o solicita un nuevo enlace.', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.email_verificado:
        flash('Tu cuenta ya está verificada. Puedes iniciar sesión.', 'info')
    else:
        user.email_verificado = True
        db.session.commit()
        flash('¡Tu correo institucional ha sido verificado con éxito! Ahora puedes iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/reenviar_verificacion', methods=['GET', 'POST'])
def reenviar_verificacion():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(email=email).first()
        if user and not user.email_verificado:
            token = user.get_token()
            msg = Message('Verifica tu correo institucional - SmartCampus UTA',
                          sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@smartcampus.com'),
                          recipients=[user.email])
            link = url_for('auth.verificar_email', token=token, _external=True)
            msg.body = f'''¡Hola {user.nombres}! Gracias por registrarte en SmartCampus UTA.
Para completar tu registro y activar tu cuenta, haz clic en el siguiente enlace:
{link}

Si tú no solicitaste este registro, ignora este correo.
'''
            try:
                mail.send(msg)
                flash('Correo de verificación reenviado. Revisa tu bandeja de entrada o spam.', 'success')
            except Exception as e:
                print("Error enviando correo:", e)
                print(f"ENLACE DE VERIFICACION (FALLBACK): {link}")
                flash('El servidor de correo de Render está bloqueado, pero tu enlace se imprimió en los logs.', 'warning')
        else:
            flash('Si el correo existe y no está verificado, se enviará un nuevo enlace.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reenviar_verificacion.html', title='Reenviar Verificación')

@bp.route('/olvide_password', methods=['GET', 'POST'])
def olvide_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = OlvidePasswordForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_token()
            msg = Message('Restablecer Contraseña - SmartCampus UTA',
                          sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@smartcampus.com'),
                          recipients=[user.email])
            link = url_for('auth.reset_password', token=token, _external=True)
            msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{link}

Si no realizaste esta solicitud, ignora este correo.
'''
            try:
                mail.send(msg)
            except Exception as e:
                print("Error enviando correo de reset:", e)
                print(f"ENLACE DE RECUPERACION (FALLBACK): {link}")
        flash('Si el correo institucional existe, recibirás instrucciones para recuperar tu contraseña.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/olvide_password.html', title='Recuperar Contraseña', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = Usuario.verify_token(token)
    if not user:
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.olvide_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Tu contraseña ha sido restablecida con éxito.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
