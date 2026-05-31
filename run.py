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

# ══════════════════════════════════════════════════════════════════════════════
# Migraciones automáticas al arrancar (Render + Aiven / XAMPP local)
# Cada ALTER TABLE corre en su propia transacción para que una columna
# ya existente no aborte las demás.
# ══════════════════════════════════════════════════════════════════════════════
_MIGRACIONES = [
    # ── tabla usuarios ────────────────────────────────────────────────────────
    "ALTER TABLE usuarios ADD COLUMN apellido VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN genero VARCHAR(10) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN fecha_nacimiento DATE NULL",
    "ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(200) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN carrera VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN facultad VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN semestre VARCHAR(50) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN foto_url VARCHAR(300) NULL",
    "ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN contacto_emergencia VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_nombre VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_telefono VARCHAR(20) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN calles_secundarias VARCHAR(200) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN direccion_lat FLOAT DEFAULT NULL",
    "ALTER TABLE usuarios ADD COLUMN direccion_lng FLOAT DEFAULT NULL",
    "ALTER TABLE usuarios ADD COLUMN cedula VARCHAR(20) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN tipo_sangre VARCHAR(50) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN zona_barrio VARCHAR(100) DEFAULT ''",
    "ALTER TABLE usuarios ADD COLUMN reputacion_promedio DECIMAL(3,2) DEFAULT 0.00",
    "ALTER TABLE usuarios ADD COLUMN total_viajes INT DEFAULT 0",
    "ALTER TABLE usuarios ADD COLUMN esta_activo TINYINT(1) DEFAULT 1",
    "ALTER TABLE usuarios ADD COLUMN es_admin TINYINT(1) DEFAULT 0",
    "ALTER TABLE usuarios ADD COLUMN email_verificado TINYINT(1) DEFAULT 0",
    "ALTER TABLE usuarios ADD COLUMN fecha_registro DATETIME NULL",
    # ── tabla viajes ──────────────────────────────────────────────────────────
    "ALTER TABLE viajes ADD COLUMN origen_lat FLOAT NULL",
    "ALTER TABLE viajes ADD COLUMN origen_lng FLOAT NULL",
    "ALTER TABLE viajes ADD COLUMN destino_lat FLOAT NULL",
    "ALTER TABLE viajes ADD COLUMN destino_lng FLOAT NULL",
    "ALTER TABLE viajes ADD COLUMN inicio_inmediato TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE viajes ADD COLUMN limite_espera_minutos INT NULL",
    "ALTER TABLE viajes ADD COLUMN created_at DATETIME NULL",
]


def _run_migrations():
    """Ejecuta cada ALTER TABLE de forma independiente (falla silenciosa si ya existe)."""
    print("=" * 52)
    print("  MIGRACIONES AUTOMÁTICAS DE BASE DE DATOS")
    print("=" * 52)
    _ok = 0
    for _sql in _MIGRACIONES:
        try:
            with db.engine.begin() as _conn:
                _conn.execute(db.text(_sql))
            _col = _sql.split("ADD COLUMN")[1].strip().split()[0]
            print(f"  ✅ Columna agregada: {_col}")
            _ok += 1
        except Exception:
            pass  # columna ya existe o tabla no existe aún → ignorar
    if _ok:
        print(f"  → {_ok} columna(s) nueva(s) agregada(s)")
    else:
        print("  → Base de datos ya estaba sincronizada")
    print("=" * 52)


# Ejecutar migraciones al importar el módulo (Gunicorn en Render lo importa)
with app.app_context():
    try:
        from app.init_db import init_database
        _run_migrations()
        init_database()
    except Exception as e:
        print(f"⚠  Error en la inicialización de DB: {e}")


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
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            print('✅ MySQL conectado correctamente')
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
