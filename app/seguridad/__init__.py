from flask import Blueprint

bp = Blueprint('seguridad', __name__)

from app.seguridad import routes  # noqa: E402, F401