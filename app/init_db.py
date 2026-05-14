"""
Inicialización de la base de datos con datos de prueba para U-Ride
"""
from app import db


def init_database():
    """Crea todas las tablas y datos iniciales"""
    db.create_all()
    # Asegurar que la columna 'direccion' existe (db.create_all no actualiza tablas existentes)
    try:
        with db.engine.connect() as conn:
            # Intentar ver si existe, si no, agregarla
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('usuarios')]
            if 'direccion' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(200) DEFAULT ''"))
                print("✅ Columna 'direccion' agregada.")
            if 'direccion_lat' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion_lat FLOAT DEFAULT NULL"))
                print("✅ Columna 'direccion_lat' agregada.")
            if 'direccion_lng' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion_lng FLOAT DEFAULT NULL"))
                print("✅ Columna 'direccion_lng' agregada.")
            if 'contacto_emergencia_nombre' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN contacto_emergencia_nombre VARCHAR(100) DEFAULT ''"))
                print("✅ Columna 'contacto_emergencia_nombre' agregada.")
            if 'contacto_emergencia_telefono' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN contacto_emergencia_telefono VARCHAR(20) DEFAULT ''"))
                print("✅ Columna 'contacto_emergencia_telefono' agregada.")
            if 'cedula' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN cedula VARCHAR(20) DEFAULT ''"))
                print("✅ Columna 'cedula' agregada.")
            if 'tipo_sangre' not in columns:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN tipo_sangre VARCHAR(50) DEFAULT ''"))
                print("✅ Columna 'tipo_sangre' agregada.")
            conn.commit()
    except Exception as e:
        print(f"⚠️ Error al verificar/agregar columna 'direccion': {e}")
    
    create_admin_user()
    print("✅ Base de datos inicializada con tablas y usuario admin.")


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
        nombre='Administrador',
        apellido='U-Ride',
        es_admin=True,
        esta_activo=True,
        email_verificado=True,
        carrera='Administración',
        zona_barrio='Centro',
        genero='',
        direccion=''
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Admin creado: {admin_email} / {admin_password}")
