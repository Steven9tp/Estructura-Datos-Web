"""
Pruebas unitarias para los modelos de U-Ride
"""
import unittest
import os
from datetime import datetime, timedelta


class TestModels(unittest.TestCase):
    """Pruebas para los modelos de datos"""

    def setUp(self):
        os.environ['FLASK_ENV'] = 'testing'
        from app import create_app, db
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.db = db

        from app.models import Usuario
        self.conductor = Usuario(
            email='conductor@uta.edu.ec',
            nombre='Conductor Test',
            carrera='Ingeniería',
            zona_barrio='Centro'
        )
        self.conductor.set_password('test123')

        self.pasajero = Usuario(
            email='pasajero@uta.edu.ec',
            nombre='Pasajero Test',
            carrera='Medicina',
            zona_barrio='Norte'
        )
        self.pasajero.set_password('test123')

        db.session.add_all([self.conductor, self.pasajero])
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def test_usuario_creacion(self):
        """Prueba: Creación correcta de usuario"""
        self.assertIsNotNone(self.conductor.id)
        self.assertEqual(self.conductor.email, 'conductor@uta.edu.ec')
        self.assertTrue(self.conductor.check_password('test123'))
        self.assertFalse(self.conductor.es_admin)

    def test_usuario_contraseña_incorrecta(self):
        """Prueba: Contraseña incorrecta devuelve False"""
        self.assertFalse(self.conductor.check_password('incorrecto'))

    def test_usuario_nivel_confianza_nuevo(self):
        """Prueba: Nivel de confianza para usuario nuevo"""
        self.assertEqual(self.conductor.obtener_nivel_confianza(), '🟡 Nuevo usuario')

    def test_viaje_creacion(self):
        """Prueba: Creación de viaje"""
        from app.models import Viaje
        viaje = Viaje(
            conductor_id=self.conductor.id,
            origen_zona='Centro',
            destino_zona='Universidad',
            fecha_hora=datetime.now() + timedelta(days=1),
            cupos_totales=4,
            cupos_disponibles=4
        )
        self.db.session.add(viaje)
        self.db.session.commit()

        self.assertIsNotNone(viaje.id)
        self.assertEqual(viaje.cupos_disponibles, 4)
        self.assertFalse(viaje.esta_lleno())
        self.assertEqual(viaje.estado, 'abierto')

    def test_solicitud_y_aceptacion(self):
        """Prueba: Solicitud para unirse a viaje y aceptación"""
        from app.models import Viaje, Solicitud
        viaje = Viaje(
            conductor_id=self.conductor.id,
            origen_zona='Centro',
            destino_zona='Universidad',
            fecha_hora=datetime.now() + timedelta(days=1),
            cupos_totales=2,
            cupos_disponibles=2
        )
        self.db.session.add(viaje)
        self.db.session.commit()

        solicitud = Solicitud(
            viaje_id=viaje.id,
            pasajero_id=self.pasajero.id
        )
        self.db.session.add(solicitud)
        self.db.session.commit()

        self.assertEqual(solicitud.estado, 'pendiente')

        viaje.aceptar_solicitud(solicitud.id)
        self.assertEqual(solicitud.estado, 'aceptada')
        self.assertEqual(viaje.cupos_disponibles, 1)

    def test_viaje_lleno(self):
        """Prueba: Viaje se marca como completo al llenarse"""
        from app.models import Viaje, Solicitud
        viaje = Viaje(
            conductor_id=self.conductor.id,
            origen_zona='Norte',
            destino_zona='Sur',
            fecha_hora=datetime.now() + timedelta(days=1),
            cupos_totales=1,
            cupos_disponibles=1
        )
        self.db.session.add(viaje)
        self.db.session.commit()

        solicitud = Solicitud(viaje_id=viaje.id, pasajero_id=self.pasajero.id)
        self.db.session.add(solicitud)
        self.db.session.commit()

        viaje.aceptar_solicitud(solicitud.id)
        self.assertTrue(viaje.esta_lleno())
        self.assertEqual(viaje.estado, 'completo')

    def test_calificacion_y_reputacion(self):
        """Prueba: Sistema de calificaciones actualiza reputación"""
        from app.models import Viaje, Solicitud, Calificacion
        viaje = Viaje(
            conductor_id=self.conductor.id,
            origen_zona='Centro',
            destino_zona='Universidad',
            fecha_hora=datetime.now() - timedelta(hours=1),
            cupos_totales=1,
            cupos_disponibles=1
        )
        self.db.session.add(viaje)
        self.db.session.commit()
        viaje.estado = 'finalizado'
        self.db.session.commit()

        calificacion = Calificacion(
            viaje_id=viaje.id,
            autor_id=self.pasajero.id,
            destinatario_id=self.conductor.id,
            puntuacion=5,
            comentario='Excelente conductor'
        )
        self.db.session.add(calificacion)
        self.db.session.commit()

        self.conductor.actualizar_reputacion()
        self.assertEqual(float(self.conductor.reputacion_promedio), 5.0)

    def test_reporte_usuario(self):
        """Prueba: Sistema de reportes"""
        from app.models import Reporte
        reporte = Reporte(
            reportante_id=self.pasajero.id,
            reportado_id=self.conductor.id,
            motivo='Comportamiento inapropiado'
        )
        self.db.session.add(reporte)
        self.db.session.commit()

        self.assertEqual(reporte.estado, 'pendiente')
        reporte.tomar_accion('Advertencia enviada')
        self.assertEqual(reporte.estado, 'accion_tomada')


if __name__ == '__main__':
    unittest.main(verbosity=2)
