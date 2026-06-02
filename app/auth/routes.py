from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.forms import LoginForm, RegistroForm
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
            tipo_usuario=form.tipo_usuario.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, te has registrado con éxito en SmartCampus!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/registro.html', title='Registro', form=form)
