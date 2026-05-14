"""
Modelos de datos para U-Ride
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# Zonas predefinidas (deben coincidir con las de los formularios)
ZONAS_VALIDAS = [
    'Centro', 'Norte', 'Sur', 'Este', 'Oeste',
    'Universidad', 'Terminal', 'Mercado Central',
    'Parque Principal', 'Hospital', 'Plaza Mayor'
]


def _utcnow():
    """Helper para obtener la hora UTC actual (compatible Python 3.12+)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), default='')
    genero = db.Column(db.String(10), default='')        # 'M', 'F', 'Otro'
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    direccion = db.Column(db.String(200), default='')
    carrera = db.Column(db.String(100))
    facultad = db.Column(db.String(100), default='')
    semestre = db.Column(db.String(50), default='')
    foto_url = db.Column(db.String(300))
    telefono = db.Column(db.String(20))
    contacto_emergencia = db.Column(db.String(100), default='') # Deprecated
    contacto_emergencia_nombre = db.Column(db.String(100), default='')
    contacto_emergencia_telefono = db.Column(db.String(20), default='')
    calles_secundarias = db.Column(db.String(200), default='')
    direccion_lat = db.Column(db.Float, nullable=True)
    direccion_lng = db.Column(db.Float, nullable=True)
    cedula = db.Column(db.String(20), default='')
    tipo_sangre = db.Column(db.String(50), default='')
    zona_barrio = db.Column(db.String(100), index=True) # Deprecated
    reputacion_promedio = db.Column(db.Numeric(3, 2), default=0.00)
    total_viajes = db.Column(db.Integer, default=0)
    esta_activo = db.Column(db.Boolean, default=True)
    es_admin = db.Column(db.Boolean, default=False)
    email_verificado = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=_utcnow)

    # Relaciones
    viajes_como_conductor = db.relationship(
        'Viaje', backref='conductor', lazy='dynamic',
        foreign_keys='Viaje.conductor_id'
    )
    solicitudes_realizadas = db.relationship(
        'Solicitud', backref='pasajero', lazy='dynamic',
        foreign_keys='Solicitud.pasajero_id'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ── Tokens seguros con itsdangerous ──────────────────────────
    def generar_token_verificacion(self):
        """Genera un token firmado para verificar el email."""
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='verificar-email')

    def generar_token_recuperacion(self):
        """Genera un token firmado para recuperar la contraseña."""
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='recuperar-password')

    @staticmethod
    def verificar_token(token, salt, max_age=86400):
        """Verifica un token firmado. Retorna el email o None si expiró/inválido.
        max_age: segundos de validez (default 24h).
        """
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt=salt, max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None
        return email

    # ── Reputación ───────────────────────────────────────────────
    def actualizar_reputacion(self):
        """Recalcula y persiste el promedio de reputacion del usuario."""
        calificaciones = Calificacion.query.filter_by(destinatario_id=self.id).all()
        if calificaciones:
            self.reputacion_promedio = round(
                sum(c.puntuacion for c in calificaciones) / len(calificaciones), 2
            )
            self.total_viajes = len(calificaciones)
        else:
            self.reputacion_promedio = 0.00
            self.total_viajes = 0
        db.session.commit()

    def obtener_nivel_confianza(self):
        """Retorna etiqueta de nivel de confianza segun reputacion."""
        rep = float(self.reputacion_promedio or 0)
        total = self.total_viajes or 0
        if total < 5:
            return 'Nuevo usuario — aun sin suficientes calificaciones'
        elif rep >= 4.5:
            return 'Excelente — usuario de alta confianza'
        elif rep >= 3.5:
            return 'Bueno — usuario confiable'
        elif rep >= 2.5:
            return 'Regular — procede con precaucion'
        else:
            return 'Precaucion — usuario con baja reputacion'

    @property
    def nombre_completo(self):
        """Retorna nombre + apellido."""
        if self.apellido:
            return f'{self.nombre} {self.apellido}'
        return self.nombre

    def __repr__(self):
        return f'<Usuario {self.nombre}>'


class Viaje(db.Model):
    __tablename__ = 'viajes'

    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    origen_zona = db.Column(db.String(100), nullable=False)
    origen_lat = db.Column(db.Float, nullable=True)
    origen_lng = db.Column(db.Float, nullable=True)
    destino_zona = db.Column(db.String(100), nullable=False)
    destino_lat = db.Column(db.Float, nullable=True)
    destino_lng = db.Column(db.Float, nullable=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, index=True)
    cupos_totales = db.Column(db.Integer, nullable=False)
    cupos_disponibles = db.Column(db.Integer, nullable=False)
    notas_reglas = db.Column(db.Text)
    # Nombre de Enum para compatibilidad con MySQL 8.4
    estado = db.Column(
        db.Enum('abierto', 'completo', 'en_curso', 'finalizado', 'cancelado',
                name='estado_viaje'),
        default='abierto', index=True
    )
    created_at = db.Column(db.DateTime, default=_utcnow)

    solicitudes = db.relationship(
        'Solicitud', backref='viaje', lazy='dynamic', cascade='all, delete-orphan'
    )

    def esta_lleno(self):
        """Retorna True si no hay cupos disponibles."""
        return self.cupos_disponibles <= 0

    def aceptar_solicitud(self, solicitud_id):
        """Acepta una solicitud si hay cupos. Retorna True si se acepto.
        NO hace commit — el caller debe hacerlo para mantener atomicidad.
        """
        if self.esta_lleno():
            return False
        solicitud = db.session.get(Solicitud, solicitud_id)
        if solicitud is None:
            return False
        solicitud.estado = 'aceptada'
        self.cupos_disponibles -= 1
        if self.cupos_disponibles <= 0:
            self.estado = 'completo'
        return True

    def cancelar_viaje(self):
        """Cancela el viaje y pone todas las solicitudes pendientes como canceladas.
        NO hace commit — el caller debe hacerlo.
        """
        self.estado = 'cancelado'
        for s in self.solicitudes.filter_by(estado='pendiente').all():
            s.estado = 'cancelada'

    def finalizar_viaje(self):
        """Marca el viaje como finalizado si esta en un estado valido.
        NO hace commit — el caller debe hacerlo.
        """
        if self.estado in ('abierto', 'completo', 'en_curso'):
            self.estado = 'finalizado'
            return True
        return False

    def __repr__(self):
        return f'<Viaje {self.id}: {self.origen_zona} -> {self.destino_zona}>'


class Solicitud(db.Model):
    __tablename__ = 'solicitudes'

    id = db.Column(db.Integer, primary_key=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viajes.id'), nullable=False)
    pasajero_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    estado = db.Column(
        db.Enum('pendiente', 'aceptada', 'rechazada', 'cancelada',
                name='estado_solicitud'),
        default='pendiente', index=True
    )
    fecha_solicitud = db.Column(db.DateTime, default=_utcnow)
    mensaje_opcional = db.Column(db.String(200))

    __table_args__ = (
        db.UniqueConstraint('viaje_id', 'pasajero_id', name='unique_solicitud'),
    )

    def rechazar(self):
        """Rechaza la solicitud y libera el cupo si estaba aceptada.
        NO hace commit — el caller debe hacerlo.
        """
        if self.estado == 'aceptada':
            self.viaje.cupos_disponibles += 1
            if self.viaje.estado == 'completo':
                self.viaje.estado = 'abierto'
        self.estado = 'rechazada'


class Calificacion(db.Model):
    __tablename__ = 'calificaciones'

    id = db.Column(db.Integer, primary_key=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viajes.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.String(300))
    fecha = db.Column(db.DateTime, default=_utcnow)


class Reporte(db.Model):
    __tablename__ = 'reportes'

    id = db.Column(db.Integer, primary_key=True)
    reportante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    reportado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    evidencia_url = db.Column(db.String(500), nullable=True)  # RF10: evidencia opcional
    estado = db.Column(
        db.Enum('pendiente', 'revisado', 'accion_tomada', name='estado_reporte'),
        default='pendiente'
    )
    tipo_sancion = db.Column(
        db.Enum('ninguna', 'advertencia', 'suspension', name='tipo_sancion_enum'),
        default='ninguna'
    )  # RF11: tipo de sancion diferenciado
    accion_tomada = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=_utcnow)

    def tomar_accion(self, descripcion_accion, tipo='ninguna'):
        """Marca el reporte como resuelto y registra la accion tomada.
        NO hace commit — el caller debe hacerlo.
        """
        self.estado = 'accion_tomada'
        self.accion_tomada = descripcion_accion
        self.tipo_sancion = tipo


class EventoTrazabilidad(db.Model):
    __tablename__ = 'eventos_trazabilidad'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viajes.id'), nullable=True)
    accion = db.Column(db.String(50), nullable=False, index=True)
    detalles = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=_utcnow, index=True)

    @classmethod
    def registrar(cls, accion, usuario_id=None, viaje_id=None, detalles=None):
        """Registra un evento de trazabilidad en la base de datos. RNF4."""
        evento = cls(
            accion=accion,
            usuario_id=usuario_id,
            viaje_id=viaje_id,
            detalles=detalles or {}
        )
        db.session.add(evento)
        # No hacemos commit aqui; el caller lo hara junto con el evento principal


class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    id = db.Column(db.Integer, primary_key=True)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viajes.id'), nullable=False)
    remitente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)

    remitente = db.relationship('Usuario', foreign_keys=[remitente_id])
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id])