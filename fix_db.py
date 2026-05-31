"""
Script para sincronizar la tabla 'usuarios' con el modelo SQLAlchemy.
Agrega las columnas que faltan en la base de datos MySQL.
"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='',
    database='u_ride_db'
)
cursor = conn.cursor()

# 1. Ver columnas actuales
cursor.execute('DESCRIBE usuarios')
columnas_actuales = [row[0] for row in cursor.fetchall()]
print("Columnas actuales en 'usuarios':")
for col in columnas_actuales:
    print(f"  - {col}")

# 2. Columnas que el modelo espera pero que podrían faltar
columnas_a_agregar = {
    'apellido': "ALTER TABLE usuarios ADD COLUMN apellido VARCHAR(100) DEFAULT '' AFTER nombre",
    'genero': "ALTER TABLE usuarios ADD COLUMN genero VARCHAR(10) DEFAULT '' AFTER apellido",
    'fecha_nacimiento': "ALTER TABLE usuarios ADD COLUMN fecha_nacimiento DATE NULL AFTER genero",
    'direccion': "ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(200) DEFAULT '' AFTER fecha_nacimiento",
    'carrera': "ALTER TABLE usuarios ADD COLUMN carrera VARCHAR(100) NULL AFTER direccion",
    'facultad': "ALTER TABLE usuarios ADD COLUMN facultad VARCHAR(100) DEFAULT '' AFTER carrera",
    'semestre': "ALTER TABLE usuarios ADD COLUMN semestre VARCHAR(50) DEFAULT '' AFTER facultad",
    'foto_url': "ALTER TABLE usuarios ADD COLUMN foto_url VARCHAR(300) NULL AFTER semestre",
    'telefono': "ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20) NULL AFTER foto_url",
    'contacto_emergencia': "ALTER TABLE usuarios ADD COLUMN contacto_emergencia VARCHAR(100) DEFAULT '' AFTER telefono",
    'contacto_emergencia_nombre': "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_nombre VARCHAR(100) DEFAULT '' AFTER contacto_emergencia",
    'contacto_emergencia_telefono': "ALTER TABLE usuarios ADD COLUMN contacto_emergencia_telefono VARCHAR(20) DEFAULT '' AFTER contacto_emergencia_nombre",
    'calles_secundarias': "ALTER TABLE usuarios ADD COLUMN calles_secundarias VARCHAR(200) DEFAULT '' AFTER contacto_emergencia_telefono",
    'direccion_lat': "ALTER TABLE usuarios ADD COLUMN direccion_lat DOUBLE NULL AFTER calles_secundarias",
    'direccion_lng': "ALTER TABLE usuarios ADD COLUMN direccion_lng DOUBLE NULL AFTER direccion_lat",
    'cedula': "ALTER TABLE usuarios ADD COLUMN cedula VARCHAR(20) DEFAULT '' AFTER direccion_lng",
    'tipo_sangre': "ALTER TABLE usuarios ADD COLUMN tipo_sangre VARCHAR(50) DEFAULT '' AFTER cedula",
    'zona_barrio': "ALTER TABLE usuarios ADD COLUMN zona_barrio VARCHAR(100) NULL AFTER tipo_sangre",
    'reputacion_promedio': "ALTER TABLE usuarios ADD COLUMN reputacion_promedio DECIMAL(3,2) DEFAULT 0.00 AFTER zona_barrio",
    'total_viajes': "ALTER TABLE usuarios ADD COLUMN total_viajes INT DEFAULT 0 AFTER reputacion_promedio",
    'esta_activo': "ALTER TABLE usuarios ADD COLUMN esta_activo TINYINT(1) DEFAULT 1 AFTER total_viajes",
    'es_admin': "ALTER TABLE usuarios ADD COLUMN es_admin TINYINT(1) DEFAULT 0 AFTER esta_activo",
    'email_verificado': "ALTER TABLE usuarios ADD COLUMN email_verificado TINYINT(1) DEFAULT 0 AFTER es_admin",
    'fecha_registro': "ALTER TABLE usuarios ADD COLUMN fecha_registro DATETIME NULL AFTER email_verificado",
}

print("\n--- Verificando columnas faltantes ---")
for col_name, alter_sql in columnas_a_agregar.items():
    if col_name not in columnas_actuales:
        print(f"  AGREGANDO columna: {col_name}")
        try:
            cursor.execute(alter_sql)
            print(f"    ✓ Columna '{col_name}' agregada exitosamente.")
        except pymysql.err.OperationalError as e:
            print(f"    ✗ Error al agregar '{col_name}': {e}")
    else:
        print(f"  ✓ Columna '{col_name}' ya existe.")

conn.commit()

# 3. Verificar también otras tablas críticas
print("\n--- Verificando tabla 'viajes' ---")
cursor.execute("SHOW TABLES LIKE 'viajes'")
if cursor.fetchone():
    cursor.execute('DESCRIBE viajes')
    cols_viajes = [row[0] for row in cursor.fetchall()]
    viajes_nuevas = {
        'origen_lat': "ALTER TABLE viajes ADD COLUMN origen_lat DOUBLE NULL AFTER origen_zona",
        'origen_lng': "ALTER TABLE viajes ADD COLUMN origen_lng DOUBLE NULL AFTER origen_lat",
        'destino_lat': "ALTER TABLE viajes ADD COLUMN destino_lat DOUBLE NULL AFTER destino_zona",
        'destino_lng': "ALTER TABLE viajes ADD COLUMN destino_lng DOUBLE NULL AFTER destino_lat",
        'inicio_inmediato': "ALTER TABLE viajes ADD COLUMN inicio_inmediato TINYINT(1) NOT NULL DEFAULT 0",
        'limite_espera_minutos': "ALTER TABLE viajes ADD COLUMN limite_espera_minutos INT NULL",
    }
    for col_name, alter_sql in viajes_nuevas.items():
        if col_name not in cols_viajes:
            print(f"  AGREGANDO columna en viajes: {col_name}")
            try:
                cursor.execute(alter_sql)
                print(f"    ✓ Columna '{col_name}' agregada.")
            except pymysql.err.OperationalError as e:
                print(f"    ✗ Error: {e}")
        else:
            print(f"  ✓ viajes.{col_name} ya existe.")
    conn.commit()
else:
    print("  ⚠ Tabla 'viajes' no existe aún.")

# 4. Verificar resultado final
cursor.execute('DESCRIBE usuarios')
columnas_finales = [row[0] for row in cursor.fetchall()]
print("\nColumnas finales en 'usuarios':")
for col in columnas_finales:
    print(f"  - {col}")

cursor.close()
conn.close()
print("\n¡Listo! La base de datos ha sido sincronizada.")
