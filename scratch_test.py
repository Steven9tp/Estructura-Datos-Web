import sys
import os

# Agregamos la ruta base para poder importar desde app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app import create_app

app = create_app()

with app.app_context():
    from flask import render_template_string
    with open('frontend/templates/reportes/imprimir_individual.html', 'r', encoding='utf-8') as f:
        template = f.read()
    try:
        # Probamos compilar el template
        app.jinja_env.compile(template)
        print("Template compila correctamente.")
    except Exception as e:
        print("Error compilando template:")
        print(e)
