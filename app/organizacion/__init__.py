from flask import Blueprint

bp = Blueprint('organizacion', __name__)

from app.organizacion import routes
