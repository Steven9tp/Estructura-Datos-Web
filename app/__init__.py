"""
Fábrica de la aplicación Flask para U-Ride
Frontend y Backend separados
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import logging

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

    # ── Garantizar MySQL exclusivamente ─────────────────────────
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'mysql' not in db_uri:
        raise RuntimeError(
            f'\n❌ ERROR: Esta aplicación SOLO funciona con MySQL.\n'
            f'   URI configurada: "{db_uri}"\n'
            f'   Asegúrate de que DATABASE_URL en .env apunte a MySQL.\n'
            f'   Ejemplo: mysql+pymysql://root:@localhost:3306/u_ride_db'
        )

    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    if HAS_MAIL and mail is not None:
        # Configurar TLS/SSL según el puerto (587=TLS, 465=SSL)
        port = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = (port == 587)
        app.config['MAIL_USE_SSL'] = (port == 465)
        app.config['MAIL_TIMEOUT'] = 10
        mail.init_app(app)

        # Log del estado del sistema de email al arrancar
        mail_user = os.getenv('MAIL_USERNAME', '').strip()
        placeholders_log = ('TU_CORREO_REAL', 'tu_correo', 'your_email', 'example')
        if mail_user and not any(p.lower() in mail_user.lower() for p in placeholders_log):
            print(f'  ✉️  Email SMTP activo: {mail_user}')
            logger.info(f'[EMAIL] SMTP configurado: {mail_user}')
        else:
            print('  ✉️  Email: modo consola DEV (sin SMTP configurado)')
            logger.info('[EMAIL] Sin SMTP → tokens impresos en terminal')

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'

    # ── Blueprints ──────────────────────────────────────────────
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.viajes import bp as viajes_bp
    app.register_blueprint(viajes_bp, url_prefix='/viajes')

    from app.seguridad import bp as seguridad_bp
    app.register_blueprint(seguridad_bp, url_prefix='/seguridad')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # ── Context processors ──────────────────────────────────────
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return {
            'now': datetime.now(),
            'reglas_seguridad': [
                'Comparte solo tu zona, no tu dirección exacta',
                'No compartas información personal sensible',
                'Respeta la puntualidad acordada',
                'Mantén comportamiento respetuoso dentro del vehículo',
                'Reporta conductas inapropiadas inmediatamente'
            ]
        }

    # ── Errores ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app