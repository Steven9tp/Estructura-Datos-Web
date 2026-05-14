"""
Configuración del proyecto U-Ride
Base de datos: MySQL exclusivamente
"""
import os
from datetime import timedelta


class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'uride-dev-secret-key-2024-cambiar-en-produccion')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Mail — Gmail SMTP (465=SSL, 587=TLS)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_TLS = (MAIL_PORT == 587)
    MAIL_USE_SSL = (MAIL_PORT == 465)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@u-ride.com')
    MAIL_TIMEOUT = 10

    # App
    DOMINIO_INSTITUCIONAL = os.getenv('DOMINIO_INSTITUCIONAL', '@uta.edu.ec')
    VIAJES_POR_PAGINA = 10


class DevelopmentConfig(Config):
    """Desarrollo con MySQL"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:@localhost:3307/u_ride_db'
    )
    # URL base para los enlaces en emails (url_for con _external=True)
    PREFERRED_URL_SCHEME = 'http'


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:@localhost:3307/u_ride_db'
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Producción con MySQL"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:@localhost:3307/u_ride_db'
    )
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # Forzar URLs seguras (https) en producción (vital para evitar filtros de spam)
    PREFERRED_URL_SCHEME = 'https'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}