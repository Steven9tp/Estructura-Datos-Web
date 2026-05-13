from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Viaje(db.Model):
    __tablename__ = 'viajes'
    # Esta línea evita el error de "Table already defined" al hacer pruebas
    __table_args__ = {'extend_existing': True} 
    
    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conductor = db.relationship('Usuario', backref='viajes_publicados')

class Reserva(db.Model):
    __tablename__ = 'reservas'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    viaje_id = db.Column(db.Integer, db.ForeignKey('viajes.id'), nullable=False)
    
    # Relaciones para conectar tablas
    pasajero = db.relationship('Usuario', backref='mis_reservas')
    viaje = db.relationship('Viaje', backref='pasajeros_reservados')