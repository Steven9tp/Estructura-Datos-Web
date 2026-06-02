"""
Modelos de datos para SmartCampus UTA Web
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# ── 1. Acceso y Personas ──────────────────────────────────────────

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    usuarios = db.relationship('Usuario', backref='rol_asignado', lazy='dynamic')

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    tipo_usuario = db.Column(db.Enum('estudiante', 'empleado', 'admin', name='tipo_usuario_enum'), default='estudiante')
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=_utcnow)
    activo = db.Column(db.Boolean, default=True)
    email_verificado = db.Column(db.Boolean, default=False)

    # Relaciones adicionales según tipo
    tramites_solicitados = db.relationship('Tramite', backref='solicitante', lazy='dynamic')
    turnos = db.relationship('Turno', backref='usuario', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    def get_token(self):
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_token(token, expires_sec=3600):
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return Usuario.query.get(user_id)

# ── 2. Procesos (Trámites y Atención) ─────────────────────────────

class Tramite(db.Model):
    __tablename__ = 'tramites'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo_tramite = db.Column(db.String(100), nullable=False) # ej: Certificado, Matrícula
    estado = db.Column(db.Enum('iniciado', 'en_revision', 'aprobado', 'rechazado', name='estado_tramite_enum'), default='iniciado')
    fecha_inicio = db.Column(db.DateTime, default=_utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    observaciones = db.Column(db.Text)

class Turno(db.Model):
    __tablename__ = 'turnos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    dependencia_id = db.Column(db.Integer, db.ForeignKey('dependencias.id'), nullable=False)
    codigo_turno = db.Column(db.String(20), nullable=False) # ej: A-001
    estado = db.Column(db.Enum('en_espera', 'atendido', 'cancelado', name='estado_turno_enum'), default='en_espera')
    fecha_emision = db.Column(db.DateTime, default=_utcnow)
    fecha_atencion = db.Column(db.DateTime, nullable=True)

# ── 3. Organización Documental ────────────────────────────────────

class Dependencia(db.Model):
    """Estructura organizativa (Árbol) Rectorado -> Facultad -> Carrera"""
    __tablename__ = 'dependencias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    dependencia_padre_id = db.Column(db.Integer, db.ForeignKey('dependencias.id'), nullable=True)
    
    subdependencias = db.relationship('Dependencia', backref=db.backref('padre', remote_side=[id]))
    turnos = db.relationship('Turno', backref='dependencia_lugar', lazy='dynamic')

class CategoriaDocumento(db.Model):
    __tablename__ = 'categorias_documento'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documentos = db.relationship('Documento', backref='categoria', lazy='dynamic')

class Documento(db.Model):
    __tablename__ = 'documentos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    ruta_archivo = db.Column(db.String(300))
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_documento.id'), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=_utcnow)

# ── 4. Rutas y Mapa (Grafo) ───────────────────────────────────────

class PuntoRuta(db.Model):
    """Nodos del Grafo (Edificios, Facultades, Puertas)"""
    __tablename__ = 'puntos_ruta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

class ConexionRuta(db.Model):
    """Aristas del Grafo"""
    __tablename__ = 'conexiones_ruta'
    id = db.Column(db.Integer, primary_key=True)
    punto_origen_id = db.Column(db.Integer, db.ForeignKey('puntos_ruta.id'), nullable=False)
    punto_destino_id = db.Column(db.Integer, db.ForeignKey('puntos_ruta.id'), nullable=False)
    distancia_metros = db.Column(db.Float, nullable=False)

# ── 5. Trazabilidad ───────────────────────────────────────────────

class HistorialAccion(db.Model):
    __tablename__ = 'historial_acciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    accion = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime, default=_utcnow)