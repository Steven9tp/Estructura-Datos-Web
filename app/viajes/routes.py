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
        viaje = Viaje(
            conductor_id=current_user.id,
            origen_zona=form.origen_zona.data,
            destino_zona=form.destino_zona.data,
            fecha_hora=form.fecha_hora.data,
            cupos_totales=form.cupos_totales.data,
            cupos_disponibles=form.cupos_totales.data,
            notas_reglas=form.notas_reglas.data
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
            detalles={'origen': form.origen_zona.data, 'destino': form.destino_zona.data,
                      'fecha': str(form.fecha_hora.data)}
        )
        db.session.commit()
        flash('¡Viaje publicado con éxito!', 'success')
        return redirect(url_for('viajes.mis_viajes'))
    return render_template('viajes/publicar.html', title='Publicar Viaje', form=form)


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
    
    return render_template('viajes/detalle.html', title='Detalle del Viaje',
                           viaje=viaje, ya_solicito=ya_solicito,
                           solicitudes_aceptadas=solicitudes_aceptadas,
                           solicitudes_pendientes=solicitudes_pendientes,
                           mensajes=mensajes)


@bp.route('/mis-viajes')
@login_required
def mis_viajes():
    viajes = Viaje.query.filter_by(
        conductor_id=current_user.id
    ).order_by(Viaje.fecha_hora.desc()).all()
    solicitudes = Solicitud.query.filter_by(
        pasajero_id=current_user.id
    ).order_by(Solicitud.fecha_solicitud.desc()).all()
    return render_template('viajes/mis_viajes.html', title='Mis Viajes',
                           viajes=viajes, solicitudes=solicitudes)


@bp.route('/solicitar/<int:viaje_id>', methods=['POST'])
@login_required
def solicitar_unirse(viaje_id):
    viaje = db.get_or_404(Viaje, viaje_id)
    if viaje.conductor_id == current_user.id:
        flash('No puedes unirte a tu propio viaje.', 'warning')
        return redirect(url_for('viajes.buscar_viajes'))
    if viaje.esta_lleno():
        flash('El viaje está lleno.', 'danger')
        return redirect(url_for('viajes.buscar_viajes'))
    ya = Solicitud.query.filter_by(viaje_id=viaje_id,
                                   pasajero_id=current_user.id).first()
    if ya:
        flash('Ya enviaste una solicitud para este viaje.', 'info')
        return redirect(url_for('viajes.buscar_viajes'))
    solicitud = Solicitud(viaje_id=viaje.id, pasajero_id=current_user.id)
    db.session.add(solicitud)
    db.session.commit()
    flash('Solicitud enviada. Espera la confirmación del conductor.', 'info')
    return redirect(url_for('viajes.detalle_viaje', viaje_id=viaje_id))


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