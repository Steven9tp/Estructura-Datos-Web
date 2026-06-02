from app import create_app, db
from app.models import Usuario, Rol # Importa para registrar en SQLAlchemy

app = create_app()

with app.app_context():
    print("Conectando a la base de datos...")
    
    # Intenta borrar todo (incluso si fallan las llaves foraneas temporalmente, 
    # db.drop_all de sqlalchemy suele manejarlo o podemos forzarlo en MySQL)
    print("Borrando tablas antiguas de U-Ride...")
    db.reflect()
    db.drop_all()
    
    print("Creando nuevas tablas de SmartCampus...")
    db.create_all()
    
    # Crear roles por defecto
    if not Rol.query.first():
        rol_estudiante = Rol(nombre='estudiante', descripcion='Estudiante regular')
        rol_empleado = Rol(nombre='empleado', descripcion='Personal administrativo')
        rol_admin = Rol(nombre='admin', descripcion='Administrador del sistema')
        db.session.add_all([rol_estudiante, rol_empleado, rol_admin])
        db.session.commit()
        print("Roles creados con éxito.")
    
    print("¡Base de datos SmartCampus inicializada correctamente!")
