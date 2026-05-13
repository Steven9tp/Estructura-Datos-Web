"""
Fábrica de la aplicación Flask para U-Ride
Frontend y Backend separados
"""
import os
import re
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

try:
    from flask_mail import Mail
    mail = Mail()
    HAS_MAIL = True
except ImportError:
    mail = None
    HAS_MAIL = False

# Rutas absolutas: frontend separado del backend
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_TEMPLATES = os.path.join(_BASE_DIR, 'frontend', 'templates')
_FRONTEND_STATIC = os.path.join(_BASE_DIR, 'frontend', 'static')


def create_app(config_name=None):
    if config_name is None:
        config_name = 'default'

    app = Flask(
        __name__,
        template_folder=_FRONTEND_TEMPLATES,
        static_folder=_FRONTEND_STATIC
    )
    app.config.from_object(config[config_name])

    # ── Configuración de Base de Datos (MySQL + SSL Aiven) ────────
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if db_uri:
        # 1. Asegurar driver pymysql
        if db_uri.startswith('mysql://'):
            db_uri = db_uri.replace('mysql://', 'mysql+pymysql://', 1)
        
        # 2. Limpieza robusta de parámetros no compatibles (ssl-mode)
        if 'ssl-mode' in db_uri:
            if '?' in db_uri:
                base_part, query_part = db_uri.split('?', 1)
                params = [p for p in query_part.split('&') if not p.startswith('ssl-mode')]
                db_uri = base_part + ('?' + '&'.join(params) if params else '')

        # 3. Forzar SSL para Aiven (PyMySQL 1.1.0+ requiere dict)
        if 'aivencloud.com' in db_uri or 'ssl' in db_uri:
            engine_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).copy()
            connect_args = engine_options.get('connect_args', {}).copy()
            connect_args['ssl'] = {} 
            engine_options['connect_args'] = connect_args
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
            
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    
    # Log de seguridad (password oculto)
    masked_uri = re.sub(r':([^@:]+)@', ':****@', db_uri)
    print(f"INFO: Base de datos configurada -> {masked_uri}")

    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    if HAS_MAIL and mail is not None:
        port = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = (port == 587)
        app.config['MAIL_USE_SSL'] = (port == 465)
        mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'

    # Registro de Blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from app.profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint, url_prefix='/perfil')

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario
    return db.session.get(Usuario, int(user_id))