from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.atencion import bp
from app.models import Turno, Dependencia
from app.estructuras.basicas import Cola
import json

# ══════════════════════════════════════════════════════════════════
# MÚLTIPLES COLAS FIFO — Una por dependencia (facultad/carrera)
# RF: Ventanilla Virtual con colas independientes por unidad académica
# ══════════════════════════════════════════════════════════════════

# Diccionario global: { dependencia_id (int) -> Cola() }
colas = {}

def get_cola(dep_id: int) -> Cola:
    """Retorna (o crea) la Cola FIFO para una dependencia dada."""
    dep_id = int(dep_id)
    if dep_id not in colas:
        colas[dep_id] = Cola()
    return colas[dep_id]


def sincronizar_colas():
    """
    Reconstruye todas las colas en memoria desde la BD.
    Se llama al inicio de cada request para garantizar consistencia.
    Solo puebla las colas que estén vacías (evita duplicados).
    """
    pendientes = (Turno.query
                  .filter_by(estado='en_espera')
                  .order_by(Turno.fecha_emision.asc())
                  .all())

    # Agrupar IDs de turnos por dependencia que ya están en su cola
    ids_en_cola = {}
    for dep_id, cola in colas.items():
        ids_en_cola[dep_id] = set(cola.a_lista())

    for turno in pendientes:
        dep_id = int(turno.dependencia_id)
        cola = get_cola(dep_id)
        if turno.id not in ids_en_cola.get(dep_id, set()):
            cola.encolar(turno.id)


def contar_en_espera(dep_id: int) -> int:
    """Cuenta turnos en_espera para una dependencia específica (desde BD)."""
    return Turno.query.filter_by(
        estado='en_espera',
        dependencia_id=int(dep_id)
    ).count()


def contar_total_espera() -> int:
    """Cuenta el total global de turnos en espera."""
    return Turno.query.filter_by(estado='en_espera').count()


# ── API: estado de cola por dependencia ──────────────────────────

@bp.route('/cola_info/<int:dep_id>')
@login_required
def cola_info(dep_id):
    """
    Endpoint JSON para consultar el estado de la cola de una dependencia.
    Usado por el frontend cuando el usuario selecciona una facultad/carrera.
    """
    sincronizar_colas()
    en_espera = contar_en_espera(dep_id)
    cola = get_cola(dep_id)
    return jsonify({
        'dep_id':    dep_id,
        'en_espera': en_espera,
        'en_cola':   len(cola),
        'tiempo_min': en_espera * 5,
    })


# ── Tomar turno ──────────────────────────────────────────────────

@bp.route('/tomar_turno', methods=['GET', 'POST'])
@login_required
def tomar_turno():
    sincronizar_colas()
    todas = Dependencia.query.all()

    # Serializar todas las dependencias como JSON para JS
    deps_json = json.dumps([{
        'id':       d.id,
        'nombre':   d.nombre,
        'padre_id': d.dependencia_padre_id
    } for d in todas])

    # Total global (banner inicial antes de que el usuario elija)
    total_espera = contar_total_espera()

    if request.method == 'POST':
        dep_id = request.form.get('dependencia_id')
        if dep_id:
            dep_id_int = int(dep_id)
            total  = Turno.query.count()
            codigo = f"A-{total + 1:03d}"

            nuevo_turno = Turno(
                usuario_id=current_user.id,
                dependencia_id=dep_id_int,
                codigo_turno=codigo
            )
            db.session.add(nuevo_turno)
            db.session.commit()

            # Encolar en la Cola FIFO de la dependencia correspondiente
            get_cola(dep_id_int).encolar(nuevo_turno.id)

            return redirect(url_for('atencion.confirmacion_turno',
                                    turno_id=nuevo_turno.id))

    return render_template('atencion/tomar_turno.html',
                           deps_json=deps_json,
                           total_espera=total_espera)


# ── Confirmación ─────────────────────────────────────────────────

@bp.route('/confirmacion/<int:turno_id>')
@login_required
def confirmacion_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    # Posición en la cola de la MISMA dependencia
    turnos_antes = Turno.query.filter(
        Turno.estado == 'en_espera',
        Turno.dependencia_id == turno.dependencia_id,
        Turno.fecha_emision < turno.fecha_emision
    ).count()
    posicion = turnos_antes + 1
    tiempo_estimado = posicion * 5
    return render_template('atencion/confirmacion.html',
                           turno=turno,
                           posicion=posicion,
                           tiempo_estimado=tiempo_estimado)


# ── Pantalla ─────────────────────────────────────────────────────

@bp.route('/pantalla')
@login_required
def pantalla():
    sincronizar_colas()
    turnos_espera   = Turno.query.filter_by(estado='en_espera').order_by(Turno.fecha_emision.asc()).all()
    turnos_atendidos= Turno.query.filter_by(estado='atendido').order_by(Turno.fecha_atencion.desc()).limit(5).all()
    dependencias = Dependencia.query.order_by(Dependencia.nombre.asc()).all()
    return render_template('atencion/pantalla.html',
                           turnos=turnos_espera,
                           atendidos=turnos_atendidos,
                           dependencias=dependencias)


# ── Atender (desencolar por dependencia) ─────────────────────────

@bp.route('/atender', methods=['POST'])
@login_required
def atender():
    # Para la defensa académica, permitimos a todos (incluidos estudiantes) simular el avance de turnos
    sincronizar_colas()

    # Opción: el admin especifica qué dependencia atender
    dep_id = request.form.get('dep_id', type=int)

    if dep_id:
        # Atender la cola de una dependencia específica
        cola = get_cola(dep_id)
        turno_id = cola.desencolar()
    else:
        # Atender el turno más antiguo de cualquier cola (FIFO global)
        turno_id = None
        turno_antiguo = Turno.query.filter_by(estado='en_espera').order_by(Turno.fecha_emision.asc()).first()
        if turno_antiguo:
            cola = get_cola(turno_antiguo.dependencia_id)
            turno_id = cola.desencolar()

    if turno_id:
        turno = db.session.get(Turno, turno_id)
        if turno and turno.estado == 'en_espera':
            from app.models import _utcnow
            turno.estado = 'atendido'
            turno.fecha_atencion = _utcnow()
            db.session.commit()
            flash(f'Turno {turno.codigo_turno} llamado a ventanilla.', 'success')
        else:
            flash('Error de sincronización, intente nuevamente.', 'warning')
    else:
        flash('No hay estudiantes en la cola de espera.', 'info')

    return redirect(url_for('atencion.pantalla'))
