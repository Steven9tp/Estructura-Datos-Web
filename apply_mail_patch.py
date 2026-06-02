import os

# 1. Update app/__init__.py
init_file = os.path.join('app', '__init__.py')
with open(init_file, 'r', encoding='utf-8') as f:
    init_content = f.read()

if 'from flask_mail import Mail' not in init_content:
    init_content = init_content.replace('from flask_login import LoginManager', 'from flask_login import LoginManager\nfrom flask_mail import Mail')
    init_content = init_content.replace('login_manager = LoginManager()', 'login_manager = LoginManager()\nmail = Mail()')
    init_content = init_content.replace('login_manager.init_app(app)', 'login_manager.init_app(app)\n    mail.init_app(app)')
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)

# 2. Update app/models.py
models_file = os.path.join('app', 'models.py')
with open(models_file, 'r', encoding='utf-8') as f:
    models_content = f.read()

if 'get_reset_password_token' not in models_content:
    models_content = models_content.replace('from flask_login import UserMixin', 'from flask_login import UserMixin\nfrom itsdangerous import URLSafeTimedSerializer as Serializer\nfrom flask import current_app')
    token_methods = """

    def get_reset_password_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_password_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return Usuario.query.get(user_id)
"""
    models_content = models_content.replace('def nombre_completo(self):\n        return f\'{self.nombres} {self.apellidos}\'', 'def nombre_completo(self):\n        return f\'{self.nombres} {self.apellidos}\'' + token_methods)
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(models_content)

# 3. Update app/forms.py
forms_file = os.path.join('app', 'forms.py')
with open(forms_file, 'r', encoding='utf-8') as f:
    forms_content = f.read()

if 'OlvidePasswordForm' not in forms_content:
    new_forms = """

class OlvidePasswordForm(FlaskForm):
    email = StringField('Correo Institucional', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Link de Recuperación')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No existe ninguna cuenta con este correo.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    confirmar_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Restablecer Contraseña')
"""
    forms_content += new_forms
    with open(forms_file, 'w', encoding='utf-8') as f:
        f.write(forms_content)

# 4. Update app/auth/routes.py
routes_file = os.path.join('app', 'auth', 'routes.py')
with open(routes_file, 'r', encoding='utf-8') as f:
    routes_content = f.read()

if 'olvide_password' not in routes_content:
    routes_content = routes_content.replace('from app.forms import LoginForm, RegistroForm', 'from app.forms import LoginForm, RegistroForm, OlvidePasswordForm, ResetPasswordForm\nfrom app import mail\nfrom flask_mail import Message')
    
    new_routes = """

@bp.route('/olvide_password', methods=['GET', 'POST'])
def olvide_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = OlvidePasswordForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_password_token()
            msg = Message('Restablecer Contraseña - SmartCampus UTA',
                          sender=current_app.config['MAIL_DEFAULT_SENDER'],
                          recipients=[user.email])
            link = url_for('auth.reset_password', token=token, _external=True)
            msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{link}

Si no realizaste esta solicitud, ignora este correo.
'''
            mail.send(msg)
            flash('Revisa tu correo institucional para obtener las instrucciones.', 'info')
            return redirect(url_for('auth.login'))
    return render_template('auth/olvide_password.html', title='Recuperar Contraseña', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = Usuario.verify_reset_password_token(token)
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
"""
    routes_content = routes_content.replace('from app import db', 'from app import db\nfrom flask import current_app')
    routes_content += new_routes
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(routes_content)

print("Patch applied successfully.")
