"""
Inicialización de la base de datos con datos de prueba para U-Ride
"""
from app import db


def init_database():
    """Crea todas las tablas y datos iniciales para SmartCampus"""
    db.create_all()
    create_admin_user()
    print("✅ Base de datos inicializada con tablas y usuario admin para SmartCampus.")

def create_admin_user():
    """Crea el usuario administrador si no existe"""
    import os
    from app.models import Usuario

    admin_email = os.getenv('ADMIN_EMAIL', 'admin@uta.edu.ec')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    if Usuario.query.filter_by(email=admin_email).first():
        print(f"ℹ️  Admin ya existe: {admin_email}")
        return

    admin = Usuario(
        email=admin_email,
        nombres='Administrador',
        apellidos='SmartCampus',
        cedula='0000000000',
        tipo_usuario='admin',
        activo=True
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Admin creado: {admin_email} / {admin_password}")
