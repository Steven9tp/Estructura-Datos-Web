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

# 3. Verificar resultado final
cursor.execute('DESCRIBE usuarios')
columnas_finales = [row[0] for row in cursor.fetchall()]
print("\nColumnas finales en 'usuarios':")
for col in columnas_finales:
    print(f"  - {col}")

cursor.close()
conn.close()
print("\n¡Listo! La base de datos ha sido sincronizada.")
