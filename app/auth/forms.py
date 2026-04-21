from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistroForm(FlaskForm):
    nombre = StringField('Nombre Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Correo Institucional', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                    validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])
    submit = SubmitField('Registrarse')
    
class LoginForm(FlaskForm):
    email = StringField('Correo Institucional', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')

from wtforms import IntegerField, FloatField # Agrega estos a tus imports arriba

class PublicarViajeForm(FlaskForm):
    origen = StringField('Punto de Partida', validators=[DataRequired()])
    destino = StringField('Punto de Llegada', validators=[DataRequired()])
    hora_salida = StringField('Hora de Salida (Ej: 07:30 AM)', validators=[DataRequired()])
    asientos = IntegerField('Asientos Disponibles', validators=[DataRequired()])
    precio = FloatField('Contribución Sugerida ($)', validators=[DataRequired()])
    submit = SubmitField('Publicar Viaje')