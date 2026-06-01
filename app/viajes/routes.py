from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.viajes import bp
from app.forms import ViajeForm, BuscarViajeForm
from app.models import Viaje, Solicitud, Mensaje, EventoTrazabilidad
from app.viajes.services import filtrar_viajes, puede_cancelar_viaje


@bp.route('/buscar', methods=['GET', 'POST'])
@login_required
def buscar_viajes():
    form = BuscarViajeForm()
    if form.validate_on_submit():
        viajes = filtrar_viajes(
            origen_zona=form.origen_zona.data,
            destino_zona=form.destino_zona.data,
            fecha=form.fecha.data,
            solo_disponibles=form.solo_disponibles.data,
        )
    else:
        viajes = filtrar_viajes()
    return render_template('viajes/buscar.html', form=form, viajes=viajes)


@bp.route('/publicar', methods=['GET', 'POST'])
@login_required
def publicar_viaje():
    form = ViajeForm()
    if form.validate_on_submit():
        from datetime import datetime as dt
        # Si es inmediato, usar hora actual; si no, usar la fecha del form
        if form.inicio_inmediato.data:
            fecha_salida = dt.now()
        else:
            if not form.fecha_hora.data:
                flash('Por favor selecciona una fecha y hora para el viaje programado.', 'danger')
                return render_template('viajes/publicar.html', title='Publicar Viaje',
                                       form=form, reglas_seguridad=[
                                           'Verifica la identidad del conductor antes de subir',
                                           'Comparte tu ubicación con alguien de confianza',
                                           'Solo viaja con conductores verificados (@uta.edu.ec)',
                                           'Usa el cinturón de seguridad siempre',
                                           'Reporta cualquier conducta inapropiada',
                                       ])
            fecha_salida = form.fecha_hora.data

        viaje = Viaje(
            conductor_id=current_user.id,
            origen_zona=form.origen_zona.data,
            destino_zona=form.destino_zona.data,
            fecha_hora=fecha_salida,
            cupos_totales=form.cupos_totales.data,
            cupos_disponibles=form.cupos_totales.data,
            notas_reglas=form.notas_reglas.data,
            inicio_inmediato=form.inicio_inmediato.data,
            limite_espera_minutos=form.limite_espera_minutos.data or None,
        )
        if form.origen_lat.data and form.origen_lng.data:
            viaje.origen_lat = float(form.origen_lat.data)
            viaje.origen_lng = float(form.origen_lng.data)
        if form.destino_lat.data and form.destino_lng.data:
            viaje.destino_lat = float(form.destino_lat.data)
            viaje.destino_lng = float(form.destino_lng.data)
            
        db.session.add(viaje)
        # RNF4: Trazabilidad de publicación
        EventoTrazabilidad.registrar(
            accion='viaje_publicado',
            usuario_id=current_user.id,
            detalles={
                'origen': form.origen_zona.data,
                'destino': form.destino_zona.data,
                'fecha': str(fecha_salida),
                'inmediato': form.inicio_inmediato.data,
                'limite_espera': form.limite_espera_minutos.data,
            }
        )
        db.session.commit()
        flash('¡Viaje publicado con éxito!', 'success')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje.id))

    reglas_seguridad = [
        'Verifica la identidad del conductor antes de subir',
        'Comparte tu ubicación con alguien de confianza',
        'Solo viaja con conductores verificados (@uta.edu.ec)',
        'Usa el cinturón de seguridad siempre',
        'Reporta cualquier conducta inapropiada',
    ]
    return render_template('viajes/publicar.html', title='Publicar Viaje',
                           form=form, reglas_seguridad=reglas_seguridad)


@bp.route('/detalle/<int:viaje_id>')
@login_required
def detalle_viaje(viaje_id):
    viaje = db.get_or_404(Viaje, viaje_id)
    ya_solicito = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        pasajero_id=current_user.id
    ).first()
    solicitudes_aceptadas = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        estado='aceptada'
    ).all()
    
    # Solo el conductor ve las solicitudes pendientes
    solicitudes_pendientes = []
    if viaje.conductor_id == current_user.id:
        solicitudes_pendientes = Solicitud.query.filter_by(
            viaje_id=viaje_id,
            estado='pendiente'
        ).all()
        
    # Obtener mensajes del viaje
    mensajes = Mensaje.query.filter_by(viaje_id=viaje_id).order_by(Mensaje.timestamp.asc()).all()
    
    # Verificar qué calificaciones ya dio el usuario en este viaje
    from app.models import Calificacion
    califs_viaje = Calificacion.query.filter_by(
        viaje_id=viaje_id, autor_id=current_user.id
    ).all()
    calificaciones_dadas = {viaje_id: {c.destinatario_id for c in califs_viaje}}

    # Reglas de seguridad para el modal
    reglas_seguridad = [
        'Verifica la identidad del conductor antes de subir',
        'Comparte tu ubicación con alguien de confianza',
        'Solo viaja con conductores verificados (@uta.edu.ec)',
        'Usa el cinturón de seguridad siempre',
        'Reporta cualquier conducta inapropiada',
    ]

    return render_template('viajes/detalle.html', title='Detalle del Viaje',
                           viaje=viaje, ya_solicito=ya_solicito,
                           solicitudes_aceptadas=solicitudes_aceptadas,
                           solicitudes_pendientes=solicitudes_pendientes,
                           mensajes=mensajes,
                           calificaciones_dadas=calificaciones_dadas,
                           reglas_seguridad=reglas_seguridad)



@bp.route('/mis-viajes')
@login_required
def mis_viajes():
    from app.models import Calificacion
    from sqlalchemy.exc import OperationalError

    # ── Safety net: migrar columnas faltantes en viajes al primer acceso ──────
    _columnas_viajes = [
        "ALTER TABLE viajes ADD COLUMN inicio_inmediato TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE viajes ADD COLUMN limite_espera_minutos INT NULL",
        "ALTER TABLE viajes ADD COLUMN created_at DATETIME NULL",
        "ALTER TABLE viajes ADD COLUMN origen_lat FLOAT NULL",
        "ALTER TABLE viajes ADD COLUMN origen_lng FLOAT NULL",
        "ALTER TABLE viajes ADD COLUMN destino_lat FLOAT NULL",
        "ALTER TABLE viajes ADD COLUMN destino_lng FLOAT NULL",
    ]
    for _sql in _columnas_viajes:
        try:
            with db.engine.begin() as _conn:
                _conn.execute(db.text(_sql))
        except Exception:
            pass  # ya existe → ignorar

    try:
        viajes = Viaje.query.filter_by(
            conductor_id=current_user.id
        ).order_by(Viaje.fecha_hora.desc()).all()

        solicitudes = Solicitud.query.filter_by(
            pasajero_id=current_user.id
        ).order_by(Solicitud.fecha_solicitud.desc()).all()

        # Precalcular pasajeros aceptados por viaje (evitar lazy queries en el template)
        # → {viaje_id: [Solicitud, ...]}
        ids_viajes_conductor = [v.id for v in viajes]
        solicitudes_aceptadas_conductor = []
        if ids_viajes_conductor:
            solicitudes_aceptadas_conductor = Solicitud.query.filter(
                Solicitud.viaje_id.in_(ids_viajes_conductor),
                Solicitud.estado == 'aceptada'
            ).all()

        pasajeros_por_viaje = {}
        for sol in solicitudes_aceptadas_conductor:
            pasajeros_por_viaje.setdefault(sol.viaje_id, []).append(sol)

        # Precalcular calificaciones dadas
        califs = Calificacion.query.filter_by(autor_id=current_user.id).all()
        calificaciones_dadas = {}
        for c in califs:
            calificaciones_dadas.setdefault(c.viaje_id, set()).add(c.destinatario_id)

        return render_template('viajes/mis_viajes.html', title='Mis Viajes',
                               viajes=viajes,
                               solicitudes=solicitudes,
                               calificaciones_dadas=calificaciones_dadas,
                               pasajeros_por_viaje=pasajeros_por_viaje)

    except OperationalError:
        db.session.rollback()
        return render_template('viajes/mis_viajes.html', title='Mis Viajes',
                               viajes=[], solicitudes=[],
                               calificaciones_dadas={},
                               pasajeros_por_viaje={})



@bp.route('/solicitar/<int:viaje_id>', methods=['POST'])
@login_required
def solicitar_unirse(viaje_id):
    viaje = db.get_or_404(Viaje, viaje_id)

    if viaje.conductor_id == current_user.id:
        flash('No puedes unirte a tu propio viaje.', 'warning')
        return redirect(url_for('viajes.buscar_viajes'))

    if viaje.cupos_disponibles <= 0 or viaje.estado not in ('abierto', 'completo'):
        flash('El viaje no tiene cupos disponibles.', 'danger')
        return redirect(url_for('viajes.buscar_viajes'))

    ya = Solicitud.query.filter_by(viaje_id=viaje_id, pasajero_id=current_user.id).first()
    if ya:
        if ya.estado == 'aceptada':
            flash('Ya estás en este viaje.', 'info')
        else:
            flash('Ya enviaste una solicitud para este viaje.', 'info')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))

    # ── Auto-aceptar: el pasajero se une directamente ──────────────────────
    solicitud = Solicitud(
        viaje_id=viaje.id,
        pasajero_id=current_user.id,
        estado='aceptada'           # se acepta automáticamente
    )
    viaje.cupos_disponibles -= 1
    if viaje.cupos_disponibles <= 0:
        viaje.estado = 'completo'

    db.session.add(solicitud)
    EventoTrazabilidad.registrar(
        accion='pasajero_unido',
        usuario_id=current_user.id,
        viaje_id=viaje.id,
        detalles={'auto_aceptado': True}
    )
    db.session.commit()
    flash('¡Te has unido al viaje exitosamente!', 'success')
    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))


@bp.route('/abandonar/<int:viaje_id>', methods=['POST'])
@login_required
def abandonar_viaje(viaje_id):
    """Pasajero abandona / cancela su lugar en un viaje."""
    viaje = db.get_or_404(Viaje, viaje_id)

    # Solo puede abandonar si el viaje aún no ha iniciado
    if viaje.estado not in ('abierto', 'completo'):
        flash('No puedes abandonar un viaje que ya está en curso o finalizado.', 'warning')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))

    solicitud = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        pasajero_id=current_user.id,
        estado='aceptada'
    ).first()

    if not solicitud:
        flash('No tienes una reserva activa en este viaje.', 'info')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))

    # Liberar el cupo y marcar la solicitud como cancelada
    solicitud.estado = 'cancelada'
    viaje.cupos_disponibles += 1
    if viaje.estado == 'completo':
        viaje.estado = 'abierto'

    EventoTrazabilidad.registrar(
        accion='pasajero_abandono',
        usuario_id=current_user.id,
        viaje_id=viaje.id,
        detalles={'viaje_origen': viaje.origen_zona, 'viaje_destino': viaje.destino_zona}
    )
    db.session.commit()
    flash('Has salido del viaje correctamente. Tu cupo quedó disponible.', 'info')
    return redirect(url_for('viajes.mis_viajes'))


@bp.route('/expulsar/<int:solicitud_id>', methods=['POST'])
@login_required
def expulsar_pasajero(solicitud_id):
    """Conductor expulsa a un pasajero del viaje."""
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    viaje = solicitud.viaje

    if viaje.conductor_id != current_user.id:
        flash('Solo el conductor puede expulsar pasajeros.', 'danger')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje.id))

    if solicitud.estado == 'aceptada':
        solicitud.estado = 'cancelada'
        viaje.cupos_disponibles += 1
        if viaje.estado == 'completo':
            viaje.estado = 'abierto'
        EventoTrazabilidad.registrar(
            accion='pasajero_expulsado',
            usuario_id=current_user.id,
            viaje_id=viaje.id,
            detalles={'pasajero_id': solicitud.pasajero_id}
        )
        db.session.commit()
        flash(f'{solicitud.pasajero.nombre} ha sido removido del viaje.', 'info')
    else:
        flash('Este pasajero ya no está activo en el viaje.', 'warning')

    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje.id))




@bp.route('/gestionar/<int:solicitud_id>/<string:accion>', methods=['POST'])
@login_required
def gestionar_solicitud(solicitud_id, accion):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    viaje = solicitud.viaje
    if viaje.conductor_id != current_user.id:
        flash('No tienes permiso para esta acción.', 'danger')
        return redirect(url_for('main.index'))
    if accion == 'aceptar':
        if viaje.aceptar_solicitud(solicitud.id):
            # RNF4: Trazabilidad aceptación (commit único al final)
            EventoTrazabilidad.registrar(
                accion='solicitud_aceptada',
                usuario_id=current_user.id,
                viaje_id=viaje.id,
                detalles={'pasajero_id': solicitud.pasajero_id, 'solicitud_id': solicitud.id}
            )
            db.session.commit()
            flash(f'Has aceptado a {solicitud.pasajero.nombre}.', 'success')
        else:
            flash('No hay cupos disponibles.', 'danger')
    elif accion == 'rechazar':
        solicitud.rechazar()
        EventoTrazabilidad.registrar(
            accion='solicitud_rechazada',
            usuario_id=current_user.id,
            viaje_id=viaje.id,
            detalles={'pasajero_id': solicitud.pasajero_id}
        )
        db.session.commit()
        flash('Solicitud rechazada.', 'info')
    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje.id))


@bp.route('/enviar-mensaje/<int:viaje_id>/<int:destinatario_id>', methods=['POST'])
@login_required
def enviar_mensaje(viaje_id, destinatario_id):
    contenido = request.form.get('contenido')
    if not contenido:
        flash('El mensaje no puede estar vacío.', 'warning')
        return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))
    
    msg = Mensaje(
        viaje_id=viaje_id,
        remitente_id=current_user.id,
        destinatario_id=destinatario_id,
        contenido=contenido
    )
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))


@bp.route('/cancelar/<int:viaje_id>', methods=['POST'])
@login_required
def cancelar_viaje(viaje_id):
    viaje = db.get_or_404(Viaje, viaje_id)
    puede, motivo = puede_cancelar_viaje(viaje, current_user.id)
    if not puede:
        flash(motivo, 'danger')
        return redirect(url_for('viajes.mis_viajes'))
    viaje.cancelar_viaje()
    # RNF4: Trazabilidad cancelación
    EventoTrazabilidad.registrar(
        accion='viaje_cancelado',
        usuario_id=current_user.id,
        viaje_id=viaje_id
    )
    db.session.commit()
    flash('Viaje cancelado correctamente.', 'info')
    return redirect(url_for('viajes.mis_viajes'))


@bp.route('/finalizar/<int:viaje_id>', methods=['POST'])
@login_required
def finalizar_viaje(viaje_id):
    viaje = db.get_or_404(Viaje, viaje_id)
    if viaje.conductor_id != current_user.id:
        flash('Solo el conductor puede finalizar el viaje.', 'danger')
        return redirect(url_for('viajes.mis_viajes'))
    if viaje.finalizar_viaje():
        # RNF4: Trazabilidad finalización
        EventoTrazabilidad.registrar(
            accion='viaje_finalizado',
            usuario_id=current_user.id,
            viaje_id=viaje_id
        )
        db.session.commit()
        flash('Viaje finalizado. ¡No olvides calificar a tus pasajeros!', 'success')
    else:
        flash('No se pudo finalizar el viaje.', 'danger')
    return redirect(url_for('viajes.mis_viajes'))


@bp.route('/iniciar/<int:viaje_id>', methods=['POST'])
@login_required
def iniciar_viaje(viaje_id):
    """Conductor inicia el viaje: estado pasa a 'en_curso'.
    Se pueden tener los asientos llenos o decidir partir con los que hay.
    """
    viaje = db.get_or_404(Viaje, viaje_id)
    if viaje.conductor_id != current_user.id:
        flash('Solo el conductor puede iniciar el viaje.', 'danger')
        return redirect(url_for('viajes.mis_viajes'))
    if viaje.iniciar_viaje():
        EventoTrazabilidad.registrar(
            accion='viaje_iniciado',
            usuario_id=current_user.id,
            viaje_id=viaje_id,
            detalles={'pasajeros_al_iniciar': viaje.cupos_totales - viaje.cupos_disponibles}
        )
        db.session.commit()
        flash('¡El viaje ha comenzado! Buen viaje.', 'success')
    else:
        flash('No se puede iniciar el viaje en su estado actual.', 'danger')
    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))