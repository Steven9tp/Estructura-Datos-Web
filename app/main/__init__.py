from flask import Blueprint

# Aquí creamos el objeto main_bp que la app busca para funcionar
main_bp = Blueprint('main', __name__)

# Importamos las rutas al final para que reconozcan el main_bp que acabamos de crear
from app.main import routes