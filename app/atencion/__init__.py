from flask import Blueprint

bp = Blueprint('atencion', __name__)

from app.atencion import routes
