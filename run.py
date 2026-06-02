#!/usr/bin/env python
"""
SmartCampus UTA Web — Punto de entrada principal
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from app.models import Usuario, Rol, Tramite, Turno, Dependencia, PuntoRuta

_env = os.getenv('FLASK_ENV', 'development')
_config_map = {'development': 'development', 'production': 'production', 'testing': 'testing'}
app = create_app(_config_map.get(_env, 'default'))

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Usuario': Usuario,
        'Rol': Rol,
        'Tramite': Tramite,
        'Turno': Turno,
        'Dependencia': Dependencia,
        'PuntoRuta': PuntoRuta
    }

@app.cli.command('init-db')
def cli_init_db():
    from app.init_db import init_database
    init_database()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
