"""
Módulo de cálculo de reputación para U-Ride
Implementa el algoritmo de confianza y reputación de usuarios
"""
from app import db


def calcular_reputacion(usuario_id: int) -> dict:
    """
    Calcula la reputación completa de un usuario

    Args:
        usuario_id (int): ID del usuario

    Returns:
        dict: Datos de reputación {promedio, total, nivel, estrellas}
    """
    from app.models import Calificacion, Usuario

    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return {'promedio': 0, 'total': 0, 'nivel': 'Desconocido', 'estrellas': '☆☆☆☆☆'}

    calificaciones = Calificacion.query.filter_by(
        destinatario_id=usuario_id
    ).all()

    if not calificaciones:
        return {
            'promedio': 0.0,
            'total': 0,
            'nivel': '🟡 Nuevo usuario',
            'estrellas': '☆☆☆☆☆'
        }

    total = len(calificaciones)
    promedio = sum(c.puntuacion for c in calificaciones) / total
    promedio = round(promedio, 2)

    # Determinar nivel de confianza
    if total < 5:
        nivel = '🟡 Nuevo usuario'
    elif promedio >= 4.5:
        nivel = '🟢 Excelente'
    elif promedio >= 3.5:
        nivel = '🔵 Bueno'
    elif promedio >= 2.5:
        nivel = '🟠 Regular'
    else:
        nivel = '🔴 Precaución'

    # Generar representación de estrellas
    estrellas_llenas = int(round(promedio))
    estrellas = '⭐' * estrellas_llenas + '☆' * (5 - estrellas_llenas)

    return {
        'promedio': promedio,
        'total': total,
        'nivel': nivel,
        'estrellas': estrellas
    }


def actualizar_reputacion_usuario(usuario_id: int) -> bool:
    """
    Recalcula y guarda la reputación de un usuario en la BD

    Args:
        usuario_id (int): ID del usuario

    Returns:
        bool: True si se actualizó correctamente
    """
    from app.models import Usuario

    datos = calcular_reputacion(usuario_id)
    usuario = db.session.get(Usuario, usuario_id)

    if not usuario:
        return False

    usuario.reputacion_promedio = datos['promedio']
    usuario.total_viajes = datos['total']
    db.session.commit()
    return True


def usuarios_con_baja_reputacion(umbral: float = 2.0) -> list:
    """
    Retorna usuarios con reputación por debajo del umbral

    Args:
        umbral (float): Puntuación mínima aceptable

    Returns:
        list: Lista de usuarios con baja reputación
    """
    from app.models import Usuario

    return Usuario.query.filter(
        Usuario.reputacion_promedio < umbral,
        Usuario.total_viajes >= 5
    ).all()


def puede_calificar(autor_id: int, viaje_id: int, destinatario_id: int) -> bool:
    """
    Verifica si un usuario puede calificar a otro en un viaje específico

    Args:
        autor_id (int): ID del autor de la calificación
        viaje_id (int): ID del viaje
        destinatario_id (int): ID del destinatario

    Returns:
        bool: True si puede calificar
    """
    from app.models import Calificacion, Viaje, Solicitud

    viaje = db.session.get(Viaje, viaje_id)
    if not viaje or viaje.estado != 'finalizado':
        return False

    # Verificar que el autor participó en el viaje
    es_conductor = viaje.conductor_id == autor_id
    es_pasajero = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        pasajero_id=autor_id,
        estado='aceptada'
    ).first() is not None

    if not (es_conductor or es_pasajero):
        return False

    # Verificar que no haya calificado ya
    ya_califico = Calificacion.query.filter_by(
        viaje_id=viaje_id,
        autor_id=autor_id,
        destinatario_id=destinatario_id
    ).first()

    return ya_califico is None
