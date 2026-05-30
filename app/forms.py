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
from flask_wtf.file import FileField, FileAllowed
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
    direccion = StringField('Dirección o Sector de residencia', validators=[
        DataRequired(message='Ingresa tu dirección o sector principal'),
        Length(max=200)
    ])
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
    origen_zona = StringField('Dirección exacta de origen',
        validators=[DataRequired(message='Escribe una dirección de origen o selecciona en el mapa')])
    
    # Coordenadas interactivas de mapa
    origen_lat = StringField('Latitud Origen', validators=[Optional()])
    origen_lng = StringField('Longitud Origen', validators=[Optional()])
    
    destino_zona = StringField('Dirección exacta de destino',
        validators=[DataRequired(message='Escribe una dirección de destino o selecciona en el mapa')])
        
    destino_lat = StringField('Latitud Destino', validators=[Optional()])
    destino_lng = StringField('Longitud Destino', validators=[Optional()])

    # Modo de salida
    inicio_inmediato = BooleanField('Publicar para salir ahora mismo', default=False)
    limite_espera_minutos = IntegerField(
        'Límite de espera (minutos)',
        validators=[Optional(), NumberRange(min=1, max=120, message='Entre 1 y 120 minutos')]
    )
    
    fecha_hora = DateTimeField('Fecha y hora de salida programada', format='%Y-%m-%dT%H:%M',
        validators=[Optional()])  # Opcional cuando inicio_inmediato=True
    cupos_totales = IntegerField('Cupos disponibles', validators=[
        DataRequired(),
        NumberRange(min=1, max=8, message='Entre 1 y 8 cupos')
    ])
    notas_reglas = TextAreaField('Notas o reglas adicionales',
        validators=[Optional(), Length(max=500)])
    submit = SubmitField('Publicar Viaje')

    def validate_fecha_hora(self, field):
        """Valida fecha solo si el viaje NO es inmediato."""
        es_inmediato = self.inicio_inmediato.data
        if not es_inmediato:
            if not field.data:
                raise ValidationError('Selecciona fecha y hora de salida, o marca \'Salir ahora\'')
            if field.data < datetime.now():
                raise ValidationError('La fecha del viaje debe ser futura (o marca \'Salir ahora\')')

    def validate_destino_zona(self, field):
        """Valida que origen y destino sean distintos."""
        if field.data and field.data == self.origen_zona.data:
            raise ValidationError('El destino debe ser diferente al origen')


class BuscarViajeForm(FlaskForm):
    """Formulario de búsqueda de viajes"""
    origen_zona = StringField('Buscar por ciudad o dirección de origen', validators=[Optional()])
    destino_zona = StringField('Buscar por ciudad o dirección de destino', validators=[Optional()])
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
    direccion = StringField('Dirección Principal (Ej: Ambato)', validators=[Optional(), Length(max=200)])
    calles_secundarias = StringField('Calles Principal y Secundaria', validators=[Optional(), Length(max=200)])
    direccion_lat = StringField('Latitud Casa', validators=[Optional()])
    direccion_lng = StringField('Longitud Casa', validators=[Optional()])
    
    # Nuevos campos de Seguridad y Verificación
    cedula = StringField('Número de Cédula/ID Estudiantil', validators=[Optional(), Length(max=20)])
    contacto_emergencia_nombre = StringField('Nombre Contacto Emergencia', validators=[Optional(), Length(max=100)])
    contacto_emergencia_telefono = StringField('Teléfono Contacto Emergencia', validators=[Optional(), Length(max=20)])
    tipo_sangre = SelectField('Tipo de Sangre', choices=[
        ('', 'No especificado'), ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')
    ], validators=[Optional()])
    
    # Información Académica
    facultad = SelectField('Facultad o Campus', choices=[
        ('', 'Selecciona tu Facultad'),
        ('Ingeniería en Sistemas, Electrónica e Industrial', 'Fisei'),
        ('Ingeniería Civil y Mecánica', 'Ficm'),
        ('Ciencias de la Salud', 'Salud'),
        ('Ciencias Administrativas', 'Administrativas'),
        ('Jurisprudencia y Ciencias Sociales', 'Jurisprudencia'),
        ('Diseño y Arquitectura', 'Diseño'),
        ('Ciencias Humanas y de la Educación', 'Educación'),
        ('Ciencias Agropecuarias', 'Agropecuarias')
    ], validators=[Optional()])
    semestre = SelectField('Semestre/Nivel', choices=[
        ('', 'Selecciona'), ('1', 'Primer Semestre'), ('2', 'Segundo Semestre'),
        ('3', 'Tercer Semestre'), ('4', 'Cuarto Semestre'), ('5', 'Quinto Semestre'),
        ('6', 'Sexto Semestre'), ('7', 'Séptimo Semestre'), ('8', 'Octavo Semestre'),
        ('9', 'Noveno Semestre'), ('10', 'Décimo Semestre'), ('Egresado', 'Egresado')
    ], validators=[Optional()])

    foto_perfil = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes (JPG, PNG)')
    ])
    submit = SubmitField('Guardar Cambios')
