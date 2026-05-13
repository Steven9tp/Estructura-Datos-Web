"""
Formularios WTForms para U-Ride
Archivo centralizado con TODOS los formularios del proyecto

Validaciones institucionales:
 - Solo correos @uta.edu.ec pueden registrarse o recuperar contraseña
 - La validación de dominio ocurre en el método validate_email() de cada form
 - Las importaciones de modelos son LAZY (dentro del método) para evitar
   importaciones circulares entre app.forms y app.models
"""
import os
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField,
    TextAreaField, IntegerField, DateTimeField, BooleanField,
    DateField, RadioField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError,
    NumberRange, Optional
)
from datetime import datetime

# Zonas predefinidas (definidas aquí para no depender de models en forms)
ZONAS_VALIDAS = [
    'Centro', 'Norte', 'Sur', 'Este', 'Oeste',
    'Universidad', 'Terminal', 'Mercado Central',
    'Parque Principal', 'Hospital', 'Plaza Mayor'
]

# Dominio institucional leído una sola vez (puede sobreescribirse desde .env)
DOMINIO_INSTITUCIONAL = os.getenv('DOMINIO_INSTITUCIONAL', '@uta.edu.ec')


def _es_correo_institucional(email: str) -> bool:
    """Retorna True si el email pertenece al dominio institucional."""
    dominio = os.getenv('DOMINIO_INSTITUCIONAL', DOMINIO_INSTITUCIONAL)
    return email.strip().lower().endswith(dominio.lower())


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class RegistroForm(FlaskForm):
    """
    Formulario de registro de usuario.

    Validaciones:
     - nombre y apellido obligatorios (2-100 caracteres)
     - email debe ser @uta.edu.ec y no estar ya registrado
     - contraseña mínimo 8 caracteres, confirmación obligatoria
    """
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    apellido = StringField('Apellido', validators=[
        DataRequired(message='El apellido es obligatorio'),
        Length(min=2, max=100, message='El apellido debe tener entre 2 y 100 caracteres')
    ])
    email = StringField('Correo institucional (@uta.edu.ec)', validators=[
        DataRequired(message='El correo es obligatorio'),
        Email(message='Ingresa un correo válido'),
        Length(max=120)
    ])
    carrera = StringField('Carrera', validators=[
        Optional(),
        Length(max=100)
    ])
    zona_barrio = SelectField('Zona/Barrio',
        choices=[('', 'Selecciona tu zona')] + [(z, z) for z in ZONAS_VALIDAS],
        validators=[DataRequired(message='Selecciona tu zona')]
    )
    telefono = StringField('Teléfono (opcional)', validators=[
        Optional(),
        Length(max=20)
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=8, message='La contraseña debe tener mínimo 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar contraseña', validators=[
        DataRequired(message='Confirma tu contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    submit = SubmitField('Registrarse')

    def validate_email(self, field):
        """
        Validación personalizada del email:
        1. Verifica que sea del dominio institucional (@uta.edu.ec)
        2. Verifica que no esté ya registrado en la BD
        """
        email = field.data.strip().lower() if field.data else ''

        # 1. Validar dominio institucional
        if not _es_correo_institucional(email):
            dominio = os.getenv('DOMINIO_INSTITUCIONAL', DOMINIO_INSTITUCIONAL)
            raise ValidationError(
                f'Solo se permite correo institucional ({dominio}). '
                f'Ejemplo: tu.nombre{dominio}'
            )

        # 2. Verificar que no exista ya (import lazy para evitar importación circular)
        from app.models import Usuario
        if Usuario.query.filter_by(email=email).first():
            raise ValidationError('Este correo ya está registrado. ¿Olvidaste tu contraseña?')


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    email = StringField('Correo institucional', validators=[
        DataRequired(message='Ingresa tu correo'),
        Email(message='Formato de correo inválido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='Ingresa tu contraseña')
    ])
    remember_me = BooleanField('Recordarme por 7 días')
    submit = SubmitField('Iniciar Sesión')


class RecuperarPasswordForm(FlaskForm):
    """
    Formulario para solicitar recuperación de contraseña.
    Solo acepta correos del dominio institucional.
    """
    email = StringField('Correo institucional', validators=[
        DataRequired(message='Ingresa tu correo institucional'),
        Email(message='Ingresa un correo válido')
    ])
    submit = SubmitField('Enviar enlace de recuperación')

    def validate_email(self, field):
        """Valida que el email sea del dominio institucional."""
        email = field.data.strip().lower() if field.data else ''
        if not _es_correo_institucional(email):
            dominio = os.getenv('DOMINIO_INSTITUCIONAL', DOMINIO_INSTITUCIONAL)
            raise ValidationError(
                f'Ingresa tu correo institucional ({dominio})'
            )


class ResetPasswordForm(FlaskForm):
    """Formulario para restablecer la contraseña usando token de recuperación"""
    password = PasswordField('Nueva contraseña', validators=[
        DataRequired(message='Ingresa tu nueva contraseña'),
        Length(min=8, message='La contraseña debe tener mínimo 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(message='Confirma tu nueva contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    submit = SubmitField('Restablecer contraseña')


# ─────────────────────────────────────────────────────────────────────────────
# Viajes
# ─────────────────────────────────────────────────────────────────────────────

class ViajeForm(FlaskForm):
    """Formulario para publicar un viaje"""
    origen_zona = SelectField('Origen (zona)',
        choices=[('', 'Selecciona origen')] + [(z, z) for z in ZONAS_VALIDAS],
        validators=[DataRequired(message='Selecciona una zona de origen')])
    destino_zona = SelectField('Destino (zona)',
        choices=[('', 'Selecciona destino')] + [(z, z) for z in ZONAS_VALIDAS],
        validators=[DataRequired(message='Selecciona una zona de destino')])
    fecha_hora = DateTimeField('Fecha y hora', format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='Selecciona fecha y hora')])
    cupos_totales = IntegerField('Cupos disponibles', validators=[
        DataRequired(),
        NumberRange(min=1, max=8, message='Entre 1 y 8 cupos')
    ])
    notas_reglas = TextAreaField('Notas o reglas adicionales',
        validators=[Optional(), Length(max=500)])
    submit = SubmitField('Publicar Viaje')

    def validate_fecha_hora(self, field):
        """Valida que la fecha del viaje sea futura."""
        if field.data and field.data < datetime.now():
            raise ValidationError('La fecha del viaje debe ser futura')

    def validate_destino_zona(self, field):
        """Valida que origen y destino sean distintos."""
        if field.data and field.data == self.origen_zona.data:
            raise ValidationError('El destino debe ser diferente al origen')


class BuscarViajeForm(FlaskForm):
    """Formulario de búsqueda de viajes"""
    origen_zona = SelectField('Origen',
        choices=[('', 'Cualquiera')] + [(z, z) for z in ZONAS_VALIDAS])
    destino_zona = SelectField('Destino',
        choices=[('', 'Cualquiera')] + [(z, z) for z in ZONAS_VALIDAS])
    fecha = DateField('Fecha del viaje', format='%Y-%m-%d', validators=[Optional()])
    solo_disponibles = BooleanField('Solo con cupos disponibles', default=True)
    submit = SubmitField('Buscar')


class SolicitudForm(FlaskForm):
    """Formulario para solicitar unirse a un viaje"""
    mensaje = TextAreaField('Mensaje para el conductor (opcional)',
        validators=[Optional(), Length(max=200)])
    submit = SubmitField('Enviar Solicitud')


# ─────────────────────────────────────────────────────────────────────────────
# Seguridad
# ─────────────────────────────────────────────────────────────────────────────

class CalificacionForm(FlaskForm):
    """Formulario para calificar a otro usuario después de un viaje"""
    puntuacion = SelectField('Puntuación', choices=[
        (5, '⭐⭐⭐⭐⭐ Excelente'),
        (4, '⭐⭐⭐⭐ Bueno'),
        (3, '⭐⭐⭐ Regular'),
        (2, '⭐⭐ Malo'),
        (1, '⭐ Pésimo')
    ], validators=[DataRequired()], coerce=int)
    comentario = TextAreaField('Comentario (opcional)',
        validators=[Optional(), Length(max=300)])
    submit = SubmitField('Enviar Calificación')


class ReporteForm(FlaskForm):
    """Formulario para reportar a un usuario"""
    motivo = SelectField('Motivo del reporte', choices=[
        ('comportamiento_inapropiado', 'Comportamiento inapropiado'),
        ('cancelacion_tardia', 'Cancelación tardía'),
        ('falta_respeto', 'Falta de respeto'),
        ('incumplimiento_reglas', 'Incumplimiento de reglas de seguridad'),
        ('otro', 'Otro motivo')
    ], validators=[DataRequired()])
    descripcion = TextAreaField('Descripción detallada', validators=[
        DataRequired(message='Describe lo sucedido'),
        Length(min=10, max=500, message='Entre 10 y 500 caracteres')
    ])
    evidencia_url = StringField(
        'Enlace de evidencia (URL de imagen/captura) — Opcional',
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField('Enviar Reporte')


# ─────────────────────────────────────────────────────────────────────────────
# Perfil
# ─────────────────────────────────────────────────────────────────────────────

class EditarPerfilForm(FlaskForm):
    """Formulario para editar perfil de usuario"""
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=100)
    ])
    apellido = StringField('Apellido', validators=[
        Optional(),
        Length(max=100)
    ])
    genero = RadioField('Género', choices=[
        ('M', 'Masculino'), ('F', 'Femenino'), ('Otro', 'Otro')
    ], default='', validators=[Optional()])
    carrera = StringField('Carrera', validators=[Optional(), Length(max=100)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d',
        validators=[Optional()])
    zona_barrio = SelectField('Zona/Barrio',
        choices=[('', 'Selecciona')] + [(z, z) for z in ZONAS_VALIDAS])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=200)])
    foto_url = StringField('URL de foto de perfil',
        validators=[Optional(), Length(max=300)])
    submit = SubmitField('Guardar Cambios')
