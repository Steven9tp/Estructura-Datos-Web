"""
Limpia las dependencias antiguas y carga las 10 facultades reales de la UTA.
Uso (con venv activado):
    venv\\Scripts\\python reset_dependencias.py
"""
from app import create_app, db
from app.models import Dependencia, CategoriaDocumento
from app.organizacion.routes import seed_dependencias
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Deshabilitar FK checks para poder truncar sin problemas de auto-referencia
    db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    db.session.execute(text("DELETE FROM dependencias"))
    db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    db.session.commit()
    print("✔  Tabla 'dependencias' limpiada.")

    # Insertar las 10 facultades reales de la UTA
    seed_dependencias()
    total = Dependencia.query.count()
    print(f"✔  Seed completado: {total} nodos (Rectorado + 10 facultades + carreras).")
