from flask import Blueprint

bp = Blueprint('tramites', __name__)

from app.tramites import routes
