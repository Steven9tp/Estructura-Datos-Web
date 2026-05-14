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

_env = os.getenv('FLASK_ENV', 'development')
_config_map = {'development': 'development', 'production': 'production', 'testing': 'testing'}
app = create_app(_config_map.get(_env, 'default'))

# Asegurar que las tablas se creen incluso cuando se usa Gunicorn en Render
with app.app_context():
    try:
        from app.init_db import init_database
        try:
            with db.engine.connect() as conn:
                print("==================================================")
                print("EJECUTANDO FIX MANUAL DE BASE DE DATOS DESDE RUN.PY")
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN contacto_emergencia_nombre VARCHAR(100) DEFAULT ''"))
                    print("✅ contacto_emergencia_nombre agregado")
                except Exception as e:
                    pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN contacto_emergencia_telefono VARCHAR(20) DEFAULT ''"))
                    print("✅ contacto_emergencia_telefono agregado")
                except Exception as e:
                    pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN calles_secundarias VARCHAR(200) DEFAULT ''"))
                    print("✅ calles_secundarias agregado")
                except Exception as e:
                    pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion_lat FLOAT DEFAULT NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion_lng FLOAT DEFAULT NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(200) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN cedula VARCHAR(20) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN tipo_sangre VARCHAR(50) DEFAULT ''"))
                except Exception: pass
                
                # Campos adicionales y obsoletos de usuarios
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN contacto_emergencia VARCHAR(100) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN zona_barrio VARCHAR(100) DEFAULT ''"))
                except Exception: pass
                
                # Campos adicionales de usuarios
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN foto_url VARCHAR(300) NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN facultad VARCHAR(100) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN semestre VARCHAR(50) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN carrera VARCHAR(100) DEFAULT ''"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20) DEFAULT ''"))
                except Exception: pass
                
                # Migraciones para tabla viajes
                try:
                    conn.execute(db.text("ALTER TABLE viajes ADD COLUMN origen_lat FLOAT NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE viajes ADD COLUMN origen_lng FLOAT NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE viajes ADD COLUMN destino_lat FLOAT NULL"))
                except Exception: pass
                try:
                    conn.execute(db.text("ALTER TABLE viajes ADD COLUMN destino_lng FLOAT NULL"))
                except Exception: pass
                
                conn.commit()
                print("==================================================")
        except Exception as ex:
            print("Error en el fix manual:", ex)
            
        init_database()
    except Exception as e:
        print(f"Error inicializando DB: {e}")
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

            from app.init_db import init_database
            try:
                init_database()
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
    print(f'🚀 http://0.0.0.0:{port}')
    print('=' * 50)
    print()
    app.run(host='0.0.0.0', port=port, debug=False)
