"""
Pruebas de integración para las rutas de U-Ride
"""
import unittest
import os


class TestRoutes(unittest.TestCase):

    def setUp(self):
        os.environ['FLASK_ENV'] = 'testing'
        from app import create_app, db
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.db = db

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def test_pagina_inicio(self):
        """Prueba: Página de inicio carga correctamente"""
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_login_page(self):
        """Prueba: Página de login carga correctamente"""
        r = self.client.get('/auth/login')
        self.assertEqual(r.status_code, 200)

    def test_registro_page(self):
        """Prueba: Página de registro carga correctamente"""
        r = self.client.get('/auth/registro')
        self.assertEqual(r.status_code, 200)

    def test_registro_usuario_valido(self):
        """Prueba: Registro exitoso de nuevo usuario"""
        r = self.client.post('/auth/registro', data={
            'nombre': 'Nuevo Estudiante',
            'email': 'nuevo@uta.edu.ec',
            'carrera': 'Derecho',
            'zona_barrio': 'Centro',
            'telefono': '099999999',
            'password': 'test123',
            'confirm_password': 'test123'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        from app.models import Usuario
        u = Usuario.query.filter_by(email='nuevo@uta.edu.ec').first()
        self.assertIsNotNone(u)

    def test_login_invalido(self):
        """Prueba: Login con credenciales incorrectas"""
        r = self.client.post('/auth/login', data={
            'email': 'noexiste@uta.edu.ec',
            'password': 'incorrecto'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_ruta_protegida_redirige(self):
        """Prueba: Ruta protegida redirige a login sin autenticar"""
        r = self.client.get('/viajes/buscar')
        self.assertEqual(r.status_code, 302)

    def test_reglas_seguridad(self):
        """Prueba: Página de reglas de seguridad accesible sin auth"""
        r = self.client.get('/seguridad/reglas-seguridad')
        self.assertEqual(r.status_code, 200)

    def test_error_404(self):
        """Prueba: Página 404 funciona"""
        r = self.client.get('/ruta/que/no/existe')
        self.assertEqual(r.status_code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
