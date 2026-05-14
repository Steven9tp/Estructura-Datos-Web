"""
API REST — U-Ride  (/api/v1/*)
Endpoints JSON: viajes, mapa (Leaflet+OSRM), estadísticas
"""
import math
from flask import jsonify
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Viaje, Usuario, Solicitud

# Coordenadas centrales por zona (Quito, Ecuador — ajustar a tu ciudad)
ZONAS_COORDS = {
    'Centro':           [-0.2299, -78.5249],
    'Norte':            [-0.1807, -78.4678],
    'Sur':              [-0.3017, -78.5522],
    'Este':             [-0.2299, -78.4678],
    'Oeste':            [-0.2299, -78.5678],
    'Universidad':      [-0.2105, -78.4925],
    'Terminal':         [-0.2448, -78.5230],
    'Mercado Central':  [-0.2305, -78.5124],
    'Parque Principal': [-0.2222, -78.5125],
    'Hospital':         [-0.2166, -78.5003],
    'Plaza Mayor':      [-0.2170, -78.5001],
}


def _haversine_km(c1, c2):
    """Calcula distancia en km entre dos puntos [lat, lon] con fórmula Haversine."""
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(6371 * 2 * math.asin(math.sqrt(a)), 1)


# ── Endpoints ─────────────────────────────────────────────────────────────

@bp.route('/viajes')
@login_required
def listar_viajes():
    """Lista de viajes disponibles (estado='abierto')."""
    viajes = (
        Viaje.query
        .filter_by(estado='abierto')
        .order_by(Viaje.fecha_hora.asc())
        .limit(20)
        .all()
    )
    return jsonify({
        'viajes': [
            {
                'id':            v.id,
                'origen':        v.origen_zona,
                'destino':       v.destino_zona,
                'fecha':         v.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'cupos':         v.cupos_disponibles,
                'cupos_totales': v.cupos_totales,
                'conductor':     v.conductor.nombre,
                'reputacion':    float(v.conductor.reputacion_promedio or 0),
                'estado':        v.estado,
            }
            for v in viajes
        ],
        'total': len(viajes),
    })


@bp.route('/viajes/<int:viaje_id>/mapa')
@login_required
def mapa_viaje(viaje_id):
    """Datos geográficos de un viaje para renderizar en Leaflet."""
    viaje = db.get_or_404(Viaje, viaje_id)

    oc = [viaje.origen_lat, viaje.origen_lng] if viaje.origen_lat else ZONAS_COORDS.get(viaje.origen_zona,  [-0.2299, -78.5249])
    dc = [viaje.destino_lat, viaje.destino_lng] if viaje.destino_lat else ZONAS_COORDS.get(viaje.destino_zona, [-0.2105, -78.4925])
    dist = _haversine_km(oc, dc)
    tiempo_min = round((dist / 40) * 60)  # Velocidad promedio ciudad: 40 km/h

    pasajeros = Solicitud.query.filter_by(
        viaje_id=viaje_id, estado='aceptada'
    ).count()

    return jsonify({
        'viaje_id': viaje.id,
        'origen':   {'zona': viaje.origen_zona,  'coords': oc},
        'destino':  {'zona': viaje.destino_zona, 'coords': dc},
        'centro':   [(oc[0] + dc[0]) / 2, (oc[1] + dc[1]) / 2],
        'distancia_km':        dist,
        'tiempo_estimado_min': tiempo_min,
        'conductor': {
            'nombre':       viaje.conductor.nombre,
            'reputacion':   float(viaje.conductor.reputacion_promedio or 0),
            'total_viajes': viaje.conductor.total_viajes,
        },
        'cupos_disponibles':   viaje.cupos_disponibles,
        'cupos_totales':       viaje.cupos_totales,
        'pasajeros_aceptados': pasajeros,
        'fecha':  viaje.fecha_hora.strftime('%d/%m/%Y %H:%M'),
        'estado': viaje.estado,
        'notas':  viaje.notas_reglas or '',
    })


@bp.route('/zonas')
def zonas():
    """Lista todas las zonas disponibles con sus coordenadas."""
    return jsonify({
        'zonas': [
            {'nombre': nombre, 'coords': coords}
            for nombre, coords in ZONAS_COORDS.items()
        ]
    })


@bp.route('/estadisticas')
@login_required
def estadisticas():
    """Métricas globales del sistema para el dashboard."""
    from app.models import Reporte, Calificacion
    return jsonify({
        'usuarios':              Usuario.query.count(),
        'viajes_activos':        Viaje.query.filter_by(estado='abierto').count(),
        'viajes_totales':        Viaje.query.count(),
        'solicitudes_aceptadas': Solicitud.query.filter_by(estado='aceptada').count(),
        'calificaciones':        Calificacion.query.count(),
        'reportes_pendientes':   Reporte.query.filter_by(estado='pendiente').count(),
    })


@bp.route('/perfil/mis-viajes')
@login_required
def mis_viajes_api():
    """Viajes del usuario autenticado (conductor y pasajero)."""
    como_conductor = (
        Viaje.query
        .filter_by(conductor_id=current_user.id)
        .order_by(Viaje.fecha_hora.desc())
        .limit(10)
        .all()
    )
    como_pasajero = (
        Solicitud.query
        .filter_by(pasajero_id=current_user.id)
        .order_by(Solicitud.fecha_solicitud.desc())
        .limit(10)
        .all()
    )
    return jsonify({
        'como_conductor': [
            {
                'id':      v.id,
                'origen':  v.origen_zona,
                'destino': v.destino_zona,
                'fecha':   v.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'estado':  v.estado,
                'cupos':   v.cupos_disponibles,
            }
            for v in como_conductor
        ],
        'como_pasajero': [
            {
                'viaje_id':         s.viaje_id,
                'origen':           s.viaje.origen_zona,
                'destino':          s.viaje.destino_zona,
                'fecha':            s.viaje.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'estado_solicitud': s.estado,
                'estado_viaje':     s.viaje.estado,
            }
            for s in como_pasajero
        ],
    })
