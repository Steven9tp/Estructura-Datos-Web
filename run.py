#!/usr/bin/env python
"""
U-Ride — Punto de entrada principal
Base de datos: MySQL (requiere MySQL activo)
Ejecutar: python run.py
"""
import os
import sys

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from app.models import Usuario, Viaje, Solicitud, Calificacion, Reporte, Mensaje, EventoTrazabilidad

# Mapear FLASK_ENV a nombre de configuración válido
_env = os.getenv('FLASK_ENV', 'development')
_config_map = {'development': 'development', 'production': 'production', 'testing': 'testing'}
app = create_app(_config_map.get(_env, 'default'))

#hola
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Usuario': Usuario,
        'Viaje': Viaje,
        'Solicitud': Solicitud,
        'Calificacion': Calificacion,
        'Reporte': Reporte,
        'Mensaje': Mensaje,
        'EventoTrazabilidad': EventoTrazabilidad,
    }


@app.cli.command('init-db')
def cli_init_db():
    """Inicializa la base de datos"""
    from app.init_db import init_database
    init_database()


@app.cli.command('create-admin')
def cli_create_admin():
    """Crea el usuario administrador"""
    from app.init_db import create_admin_user
    create_admin_user()


if __name__ == '__main__':
    print()
    print('=' * 50)
    print('  🚗 U-Ride — Carpooling Universitario UTA')
    print('  📦 Base de datos: MySQL')
    print('=' * 50)

    with app.app_context():
        try:
            # Verificar conexión a MySQL
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            print('✅ MySQL conectado correctamente')

            db.create_all()
            from app.init_db import create_admin_user
            try:
                create_admin_user()
            except Exception:
                db.session.rollback()
            print('✅ Tablas listas')

        except Exception as e:
            print()
            print(f'❌ ERROR: No se puede conectar a MySQL')
            print(f'   Detalle: {e}')
            print()
            print('   Verifica que:')
            print('   1. MySQL está ENCENDIDO')
            print('   2. La BD "u_ride_db" existe:')
            print('      mysql -u root -e "CREATE DATABASE u_ride_db;"')
            print('   3. .env tiene la URL correcta')
            print()
            sys.exit(1)

    port = int(os.getenv('PORT', 5000))
    dominio = os.getenv('DOMINIO_INSTITUCIONAL', '@uta.edu.ec')
    print(f'🎓 Dominio: {dominio}')
    print(f'👤 Admin: admin{dominio} / admin123')
    print(f'🚀 http://127.0.0.1:{port}')
    print('=' * 50)
    print()
    app.run(host='127.0.0.1', port=port, debug=True)