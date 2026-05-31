"""
Script para sincronizar la tabla 'usuarios' con el modelo SQLAlchemy.
Agrega las columnas que faltan en la base de datos MySQL (XAMPP puerto 3307).
"""
import pymysql
import sys

# ── Configuración de conexión (XAMPP usa puerto 3307) ──────────────────────
DB_CONFIG = dict(
    host='localhost',
    port=3307,          # XAMPP usa 3307 por defecto
    user='root',
    password='',        # sin contraseña en XAMPP
    database='u_ride_db'
)

print("=" * 55)
print("  U-Ride — Sincronización de Base de Datos")
print("=" * 55)
print(f"  Conectando a: localhost:{DB_CONFIG['port']}/u_ride_db")

try:
    conn = pymysql.connect(**DB_CONFIG)
except Exception as e:
    print(f"\n❌ ERROR: No se pudo conectar a MySQL")
    print(f"   {e}")
    print("\n   Verifica que XAMPP esté encendido y MySQL activo.")
    sys.exit(1)

cursor = conn.cursor()
print("  ✅ Conexión exitosa\n")

# ── 1. Verificar que la BD existe ──────────────────────────────────────────
cursor.execute("SHOW TABLES LIKE 'usuarios'")
if not cursor.fetchone():
    print("⚠  La tabla 'usuarios' no existe. Inicia el servidor Flask primero.")
    print("   python run.py  (crea las tablas automáticamente)")
    cursor.close()
    conn.close()
    sys.exit(1)

# ── 2. Ver columnas actuales ───────────────────────────────────────────────
cursor.execute('DESCRIBE usuarios')
columnas_actuales = [row[0] for row in cursor.fetchall()]
print("Columnas actuales en 'usuarios':")
for col in columnas_actuales:
    print(f"  - {col}")

# ── 3. Columnas que el modelo requiere ────────────────────────────────────
columnas_a_agregar = {
    'apellido':                     "ALTER TABLE usuarios ADD COLUMN apellido VARCHAR(100) DEFAULT '' AFTER nombre",
    'genero':                       "ALTER TABLE usuarios ADD COLUMN genero VARCHAR(10) DEFAULT '' AFTER apellido",
    'fecha_nacimiento':             "ALTER TABLE usuarios ADD COLUMN fecha_nacimiento DATE NULL AFTER genero",
    'direccion':                    "ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(200) DEFAULT ''",
    'carrera':                      "ALTER TABLE usuarios ADD COLUMN carrera VARCHAR(100) NULL",
    'facultad':                     "ALTER TABLE usuarios ADD COLUMN facultad VARCHAR(100) DEFAULT ''",
    'semestre':                     "ALTER TABLE usuarios ADD COLUMN semestre VARCHAR(50) DEFAULT ''",
    'foto_url':                     "ALTER TABLE usuarios ADD COLUMN foto_url VARCHAR(300) NULL",
    'telefono':                     "ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20) NULL",
    'contacto_emergencia':          "ALTER TABLE usuarios ADD COLUMN contacto_emergencia VARCHAR(100) DEFAULT ''",
    'contacto_emergencia_nombre':   "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_nombre VARCHAR(100) DEFAULT ''",
    'contacto_emergencia_telefono': "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_telefono VARCHAR(20) DEFAULT ''",
    'calles_secundarias':           "ALTER TABLE usuarios ADD COLUMN calles_secundarias VARCHAR(200) DEFAULT ''",
    'direccion_lat':                "ALTER TABLE usuarios ADD COLUMN direccion_lat FLOAT NULL",
    'direccion_lng':                "ALTER TABLE usuarios ADD COLUMN direccion_lng FLOAT NULL",
    'cedula':                       "ALTER TABLE usuarios ADD COLUMN cedula VARCHAR(20) DEFAULT ''",
    'tipo_sangre':                  "ALTER TABLE usuarios ADD COLUMN tipo_sangre VARCHAR(50) DEFAULT ''",
    'zona_barrio':                  "ALTER TABLE usuarios ADD COLUMN zona_barrio VARCHAR(100) NULL",
    'reputacion_promedio':          "ALTER TABLE usuarios ADD COLUMN reputacion_promedio DECIMAL(3,2) DEFAULT 0.00",
    'total_viajes':                 "ALTER TABLE usuarios ADD COLUMN total_viajes INT DEFAULT 0",
    'esta_activo':                  "ALTER TABLE usuarios ADD COLUMN esta_activo TINYINT(1) DEFAULT 1",
    'es_admin':                     "ALTER TABLE usuarios ADD COLUMN es_admin TINYINT(1) DEFAULT 0",
    'email_verificado':             "ALTER TABLE usuarios ADD COLUMN email_verificado TINYINT(1) DEFAULT 0",
    'fecha_registro':               "ALTER TABLE usuarios ADD COLUMN fecha_registro DATETIME NULL",
}

print("\n--- Verificando columnas faltantes en 'usuarios' ---")
cambios = 0
for col_name, alter_sql in columnas_a_agregar.items():
    if col_name not in columnas_actuales:
        try:
            cursor.execute(alter_sql)
            print(f"  ✅ AGREGADA: {col_name}")
            cambios += 1
        except pymysql.err.OperationalError as e:
            print(f"  ❌ Error al agregar '{col_name}': {e}")
    else:
        print(f"  ✓  Ya existe: {col_name}")

conn.commit()

# ── 4. Tabla viajes ────────────────────────────────────────────────────────
cursor.execute("SHOW TABLES LIKE 'viajes'")
if cursor.fetchone():
    cursor.execute('DESCRIBE viajes')
    cols_viajes = [row[0] for row in cursor.fetchall()]
    print("\n--- Verificando columnas faltantes en 'viajes' ---")
    viajes_nuevas = {
        'origen_lat':            "ALTER TABLE viajes ADD COLUMN origen_lat FLOAT NULL",
        'origen_lng':            "ALTER TABLE viajes ADD COLUMN origen_lng FLOAT NULL",
        'destino_lat':           "ALTER TABLE viajes ADD COLUMN destino_lat FLOAT NULL",
        'destino_lng':           "ALTER TABLE viajes ADD COLUMN destino_lng FLOAT NULL",
        'inicio_inmediato':      "ALTER TABLE viajes ADD COLUMN inicio_inmediato TINYINT(1) NOT NULL DEFAULT 0",
        'limite_espera_minutos': "ALTER TABLE viajes ADD COLUMN limite_espera_minutos INT NULL",
    }
    for col_name, alter_sql in viajes_nuevas.items():
        if col_name not in cols_viajes:
            try:
                cursor.execute(alter_sql)
                print(f"  ✅ AGREGADA en viajes: {col_name}")
                cambios += 1
            except pymysql.err.OperationalError as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"  ✓  Ya existe en viajes: {col_name}")
    conn.commit()

cursor.close()
conn.close()

print("\n" + "=" * 55)
if cambios > 0:
    print(f"  ✅ {cambios} columna(s) agregada(s) exitosamente.")
    print("  ➡  Reinicia el servidor Flask ahora: python run.py")
else:
    print("  ✅ Base de datos ya estaba sincronizada.")
    print("  ➡  Si el error persiste, reinicia Flask: python run.py")
print("=" * 55)
