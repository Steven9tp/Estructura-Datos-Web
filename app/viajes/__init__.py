from flask import Blueprint

bp = Blueprint('viajes', __name__)

from app.viajes import routes  # noqa: E402, F401