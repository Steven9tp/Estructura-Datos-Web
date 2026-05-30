from app import create_app, db
# pyrefly: ignore [missing-import]
from sqlalchemy import text

app = create_app()

def upgrade():
    with app.app_context():
        print("Conectando a la base de datos...")
        try:
            # Lista de comandos ALTER TABLE para añadir las nuevas columnas
            comandos = [
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cedula VARCHAR(20) DEFAULT '';",
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS contacto_emergencia VARCHAR(100) DEFAULT '';",
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo_sangre VARCHAR(50) DEFAULT '';",
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS facultad VARCHAR(100) DEFAULT '';",
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS semestre VARCHAR(50) DEFAULT '';",
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS origen_lat FLOAT NULL;",
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS origen_lng FLOAT NULL;",
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS destino_lat FLOAT NULL;",
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS destino_lng FLOAT NULL;",
                # Nuevos campos: modo de salida inmediata y límite de espera
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS inicio_inmediato TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE viajes ADD COLUMN IF NOT EXISTS limite_espera_minutos INT NULL;"
            ]
            
            for cmd in comandos:
                print(f"Ejecutando: {cmd}")
                db.session.execute(text(cmd))
            
            db.session.commit()
            print("✅ Base de datos actualizada con éxito. Nuevos campos de Seguridad y Académicos añadidos.")
            
        except Exception as e:
            print(f"❌ Error al actualizar la base de datos: {e}")
            db.session.rollback()

if __name__ == "__main__":
    upgrade()
