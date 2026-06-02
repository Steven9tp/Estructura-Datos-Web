from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import Usuario

class LoginForm(FlaskForm):
    email = StringField('Correo Institucional', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Ingresar')

class RegistroForm(FlaskForm):
    nombres = StringField('Nombres', validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(min=2, max=100)])
    cedula = StringField('Cédula / ID', validators=[DataRequired(), Length(min=10, max=20)])
    email = StringField('Correo Institucional', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirmar_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    tipo_usuario = SelectField('Tipo de Usuario', choices=[('estudiante', 'Estudiante'), ('empleado', 'Empleado / Docente')])
    submit = SubmitField('Registrarse')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Por favor, usa un correo electrónico diferente. Este ya está registrado.')

    def validate_cedula(self, cedula):
        user = Usuario.query.filter_by(cedula=cedula.data).first()
        if user:
            raise ValidationError('Esta cédula ya se encuentra registrada en el sistema.')

class SolicitarTramiteForm(FlaskForm):
    tipo_tramite = SelectField('Tipo de Trámite', choices=[
        ('certificado_matricula', 'Certificado de Matrícula'),
        ('solicitud_especie', 'Solicitud de Especie Valorada'),
        ('justificacion_falta', 'Justificación de Falta'),
        ('retiro_asignatura', 'Retiro de Asignatura')
    ])
    observaciones = TextAreaField('Observaciones (Opcional)', validators=[Length(max=500)])
    submit = SubmitField('Generar Solicitud')

class GenerarTurnoForm(FlaskForm):
    dependencia_id = SelectField('Dependencia / Ventanilla', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Tomar Turno Virtual')
