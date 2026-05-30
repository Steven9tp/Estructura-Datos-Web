"""
Módulo de seguridad — Calificaciones y reportes
"""
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.seguridad import bp
from app.forms import CalificacionForm, ReporteForm
from app.models import Viaje, Solicitud, Calificacion, Reporte, Usuario


@bp.route('/reglas-seguridad')
def reglas_seguridad():
    """Muestra las reglas de seguridad de U-Ride"""
    return render_template('seguridad/reglas.html', title='Reglas de Seguridad')


@bp.route('/calificar/<int:viaje_id>/<int:destinatario_id>', methods=['GET', 'POST'])
@login_required
def calificar(viaje_id, destinatario_id):
    """Permite calificar a otro usuario después de un viaje.
    
    RF8: Solo puede calificar quien participó efectivamente:
      - El conductor puede calificar a los pasajeros aceptados.
      - Un pasajero aceptado puede calificar al conductor.
    """
    viaje = db.get_or_404(Viaje, viaje_id)
    destinatario = db.get_or_404(Usuario, destinatario_id)

    # Solo si el viaje está finalizado
    if viaje.estado != 'finalizado':
        flash('Solo puedes calificar después de finalizar el viaje.', 'warning')
        return redirect(url_for('viajes.mis_viajes'))

    # ── Validación de participación efectiva (corrección obs. 3) ──────────────
    es_conductor = (viaje.conductor_id == current_user.id)
    solicitud_autor = Solicitud.query.filter_by(
        viaje_id=viaje_id,
        pasajero_id=current_user.id,
        estado='aceptada'
    ).first()
    es_pasajero_aceptado = solicitud_autor is not None

    if not es_conductor and not es_pasajero_aceptado:
        flash('Solo los participantes del viaje pueden calificar.', 'danger')
        return redirect(url_for('viajes.mis_viajes'))

    # El conductor solo puede calificar a pasajeros aceptados
    if es_conductor:
        es_destinatario_valido = Solicitud.query.filter_by(
            viaje_id=viaje_id,
            pasajero_id=destinatario_id,
            estado='aceptada'
        ).first() is not None
        if not es_destinatario_valido:
            flash('Solo puedes calificar a los pasajeros de este viaje.', 'danger')
            return redirect(url_for('viajes.mis_viajes'))

    # El pasajero solo puede calificar al conductor
    if es_pasajero_aceptado and not es_conductor:
        if destinatario_id != viaje.conductor_id:
            flash('Como pasajero solo puedes calificar al conductor del viaje.', 'danger')
            return redirect(url_for('viajes.mis_viajes'))
    # ─────────────────────────────────────────────────────────────────────────

    # Verificar que no haya calificado antes
    ya_califico = Calificacion.query.filter_by(
        viaje_id=viaje_id,
        autor_id=current_user.id,
        destinatario_id=destinatario_id
    ).first()
    if ya_califico:
        flash('Ya has calificado a este usuario para este viaje.', 'info')
        return redirect(url_for('viajes.mis_viajes'))

    form = CalificacionForm()
    if form.validate_on_submit():
        calificacion = Calificacion(
            viaje_id=viaje_id,
            autor_id=current_user.id,
            destinatario_id=destinatario_id,
            puntuacion=form.puntuacion.data,
            comentario=form.comentario.data
        )
        db.session.add(calificacion)
        db.session.commit()
        destinatario.actualizar_reputacion()
        flash('¡Calificación enviada!', 'success')
        return redirect(url_for('viajes.mis_viajes'))

    return render_template('seguridad/calificar.html', title='Calificar Usuario',
                           form=form, destinatario=destinatario, viaje=viaje)


@bp.route('/reportar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def reportar(usuario_id):
    """Permite reportar a un usuario por conducta indebida"""
    reportado = db.get_or_404(Usuario, usuario_id)
    form = ReporteForm()
    if form.validate_on_submit():
        reporte = Reporte(
            reportante_id=current_user.id,
            reportado_id=usuario_id,
            motivo=f"{form.motivo.data}: {form.descripcion.data}",
            evidencia_url=form.evidencia_url.data or None  # RF10: evidencia opcional
        )
        db.session.add(reporte)
        db.session.commit()
        flash('Reporte enviado. El equipo lo revisará pronto.', 'success')
        return redirect(url_for('main.index'))
    return render_template('seguridad/reportar.html', title='Reportar Usuario',
                           form=form, reportado=reportado)