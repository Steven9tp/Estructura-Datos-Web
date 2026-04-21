from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # <--- IMPORTANTE
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager() # <--- IMPORTANTE
login_manager.login_view = 'main.login' # Define a dónde ir si no está logueado

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app) # <--- IMPORTANTE

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.Usuario.query.get(int(user_id))

    from app.main.routes import main_bp
    app.register_blueprint(main_bp)

    return app