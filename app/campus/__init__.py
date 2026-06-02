from flask import Blueprint

bp = Blueprint('campus', __name__)

from app.campus import routes
