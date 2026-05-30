"""
Servicios de negocio para la gestión de viajes
Lógica de búsqueda, filtrado y actualización de cupos
"""
from datetime import datetime
from app.models import Viaje, Solicitud


def _extraer_termino_busqueda(texto: str, max_palabras: int = 2) -> str:
    """
    Extrae un término corto de búsqueda a partir de un texto libre.
    
    Nominatim devuelve strings como:
      "Ficoa, Ambato, Tungurahua, Ecuador"
    Tomamos las primeras N palabras significativas (sin comas) para el LIKE.
    
    Args:
        texto: Dirección completa ingresada por el usuario
        max_palabras: Máximo de palabras a usar como término
    Returns:
        Término limpio para usar en ilike('%termino%')
    """
    # Quitar comas y separar por espacios
    partes = [p.strip() for p in texto.replace(',', ' ').split() if p.strip()]
    # Tomar las primeras max_palabras palabras
    termino = ' '.join(partes[:max_palabras])
    return termino if termino else texto.strip()


def filtrar_viajes(origen_zona=None, destino_zona=None, fecha=None, solo_disponibles=True):
    """
    Filtra los viajes disponibles según criterios de búsqueda

    Args:
        origen_zona (str): Zona de origen
        destino_zona (str): Zona de destino
        fecha (date): Fecha del viaje (objeto date de Python)
        solo_disponibles (bool): Si True, solo muestra viajes con cupos > 0

    Returns:
        list: Lista de viajes que cumplen los criterios
    """
    query = Viaje.query.filter(
        Viaje.estado == 'abierto',
        Viaje.fecha_hora > datetime.now(),
    )

    if solo_disponibles:
        query = query.filter(Viaje.cupos_disponibles > 0)

    if origen_zona and origen_zona.strip():
        # RF4: Búsqueda parcial insensible a mayúsculas para admitir texto libre (Nominatim)
        termino_origen = _extraer_termino_busqueda(origen_zona)
        query = query.filter(Viaje.origen_zona.ilike(f'%{termino_origen}%'))

    if destino_zona and destino_zona.strip():
        termino_destino = _extraer_termino_busqueda(destino_zona)
        query = query.filter(Viaje.destino_zona.ilike(f'%{termino_destino}%'))

    if fecha:
        inicio_dia = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
        fin_dia = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
        query = query.filter(Viaje.fecha_hora.between(inicio_dia, fin_dia))

    return query.order_by(Viaje.fecha_hora.asc()).all()


def actualizar_cupos(viaje_id: int) -> bool:
    """
    Recalcula los cupos disponibles de un viaje
    basándose en las solicitudes aceptadas

    Args:
        viaje_id (int): ID del viaje

    Returns:
        bool: True si se actualizó correctamente
    """
    from app import db

    viaje = db.session.get(Viaje, viaje_id)
    if not viaje:
        return False

    aceptadas = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        estado='aceptada'
    ).count()

    viaje.cupos_disponibles = viaje.cupos_totales - aceptadas

    if viaje.cupos_disponibles <= 0:
        viaje.estado = 'completo'
    elif viaje.estado == 'completo' and viaje.cupos_disponibles > 0:
        viaje.estado = 'abierto'

    db.session.commit()
    return True


def obtener_pasajeros_aceptados(viaje_id: int) -> list:
    """
    Retorna la lista de pasajeros aceptados en un viaje

    Args:
        viaje_id (int): ID del viaje

    Returns:
        list: Lista de usuarios aceptados
    """
    solicitudes = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        estado='aceptada'
    ).all()
    return [s.pasajero for s in solicitudes]


def puede_cancelar_viaje(viaje, usuario_id: int) -> tuple:
    """
    Verifica si un usuario puede cancelar un viaje

    Args:
        viaje: Objeto Viaje
        usuario_id (int): ID del usuario

    Returns:
        tuple: (bool, str) - Puede cancelar y motivo
    """
    from datetime import timedelta

    if viaje.conductor_id != usuario_id:
        return False, 'Solo el conductor puede cancelar el viaje'

    if viaje.estado in ['finalizado', 'cancelado']:
        return False, 'El viaje ya no puede ser cancelado'

    limite_horas = 2
    tiempo_restante = viaje.fecha_hora - datetime.now()
    if tiempo_restante < timedelta(hours=limite_horas):
        return False, f'Solo se puede cancelar con {limite_horas} horas de anticipación'

    return True, 'OK'


def viajes_recientes_conductor(conductor_id: int, limite: int = 5) -> list:
    """
    Retorna los viajes más recientes de un conductor

    Args:
        conductor_id (int): ID del conductor
        limite (int): Número máximo de viajes a retornar

    Returns:
        list: Lista de viajes recientes
    """
    return Viaje.query.filter_by(
        conductor_id=conductor_id
    ).order_by(Viaje.fecha_hora.desc()).limit(limite).all()
