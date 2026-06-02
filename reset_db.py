from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text
from app.init_db import init_database

print("Iniciando limpieza de la base de datos...")
app = create_app()

with app.app_context():
    # Desactivar protección de llaves foráneas para borrar sin problemas
    # Debe ser en la misma conexión exacta que usa drop_all
    with db.engine.connect() as conn:
        conn.execute(text('SET FOREIGN_KEY_CHECKS=0;'))
        db.metadata.drop_all(bind=conn)
        conn.execute(text('SET FOREIGN_KEY_CHECKS=1;'))
        conn.commit()
    
    print("Tablas borradas. Creando nueva estructura...")
    # Reconstruir la base de datos limpia
    init_database()
