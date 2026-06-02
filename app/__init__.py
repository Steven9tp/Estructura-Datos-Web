"""
Fábrica de la aplicación Flask para SmartCampus
"""
import os
import re
import logging
import socket
socket.setdefaulttimeout(5.0)
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config

logger = logging.getLogger(__name__)
import sys
logging.basicConfig(level=logging.ERROR, handlers=[logging.StreamHandler(sys.stdout)])

from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_TEMPLATES = os.path.join(_BASE_DIR, 'frontend', 'templates')
_FRONTEND_STATIC = os.path.join(_BASE_DIR, 'frontend', 'static')

def create_app(config_name=None):
    if config_name is None: config_name = 'default'
    app = Flask(__name__, template_folder=_FRONTEND_TEMPLATES, static_folder=_FRONTEND_STATIC)
    app.config.from_object(config[config_name])
    # Forzar recarga de archivos estáticos en desarrollo
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('mysql://'): db_uri = db_uri.replace('mysql://', 'mysql+pymysql://', 1)
    # PyMySQL no soporta el parámetro ssl-mode con guion, lo quitamos porque negocia TLS automáticamente
    if '?ssl-mode=REQUIRED' in db_uri:
        db_uri = db_uri.replace('?ssl-mode=REQUIRED', '')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.atencion import bp as atencion_bp
    app.register_blueprint(atencion_bp, url_prefix='/atencion')
    from app.organizacion import bp as organizacion_bp
    app.register_blueprint(organizacion_bp, url_prefix='/organizacion')
    from app.campus import bp as campus_bp
    app.register_blueprint(campus_bp, url_prefix='/campus')
    from app.tramites import bp as tramites_bp
    app.register_blueprint(tramites_bp, url_prefix='/tramites')

    @app.after_request
    def add_no_cache(response):
        """Evitar caché de CSS/JS durante desarrollo."""
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario
    return db.session.get(Usuario, int(user_id))