from app import create_app, db
from app.models import Usuario # <--- AGREGA ESTA LÍNEA

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)