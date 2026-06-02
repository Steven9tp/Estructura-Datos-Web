from flask import render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app import db
from app.tramites import bp
from app.models import Tramite, HistorialAccion
from app.forms import SolicitarTramiteForm

ESTADOS_VALIDOS = ['iniciado', 'en_revision', 'aprobado', 'rechazado']
TIPOS_TRAMITE = {
    'certificado_matricula': 'Certificado de Matrícula',
    'solicitud_especie': 'Solicitud de Especie Valorada',
    'justificacion_falta': 'Justificación de Falta',
    'retiro_asignatura': 'Retiro de Asignatura',
}

@bp.route('/solicitar', methods=['GET', 'POST'])
@login_required
def solicitar():
    form = SolicitarTramiteForm()
    if form.validate_on_submit():
        nuevo = Tramite(
            usuario_id=current_user.id,
            tipo_tramite=form.tipo_tramite.data,
            observaciones=form.observaciones.data,
            estado='iniciado'
        )
        db.session.add(nuevo)
        db.session.add(HistorialAccion(
            usuario_id=current_user.id,
            accion=f"Creó solicitud: {TIPOS_TRAMITE.get(form.tipo_tramite.data, form.tipo_tramite.data)}"
        ))
        db.session.commit()
        flash('¡Trámite registrado! Será atendido a la brevedad.', 'success')
        return redirect(url_for('tramites.historial'))
    return render_template('tramites/solicitar.html', form=form)


@bp.route('/historial')
@login_required
def historial():
    filtro_estado = request.args.get('estado', 'todos')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if current_user.tipo_usuario == 'estudiante':
        q = Tramite.query.filter_by(usuario_id=current_user.id)
    else:
        q = Tramite.query

    if filtro_estado != 'todos' and filtro_estado in ESTADOS_VALIDOS:
        q = q.filter_by(estado=filtro_estado)

    q = q.order_by(Tramite.fecha_inicio.desc())
    paginacion = q.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'tramites/historial.html',
        tramites=paginacion.items,
        paginacion=paginacion,
        filtro_estado=filtro_estado,
        estados=ESTADOS_VALIDOS,
    )


from app.estructuras.basicas import Pila

@bp.route('/bitacora')
@login_required
def bitacora():
    if current_user.tipo_usuario == 'estudiante':
        flash('Acceso denegado. Solo personal autorizado.', 'danger')
        return redirect(url_for('main.index'))
    
    # ── INTEGRACIÓN DE PILA (LIFO) ──
    # Cargamos el historial reciente en una Pila para permitir "Deshacer"
    logs_db = HistorialAccion.query.order_by(HistorialAccion.fecha.asc()).all()
    pila_historial = Pila()
    for log in logs_db[-50:]: # Cargamos los últimos 50 a la pila
        pila_historial.apilar(log)
    
    page = request.args.get('page', 1, type=int)
    paginacion = HistorialAccion.query.order_by(
        HistorialAccion.fecha.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Pasamos el tope de la pila al template para saber qué se puede deshacer
    ultimo_evento = pila_historial.ver_tope()

    return render_template('tramites/bitacora.html', 
                           logs=paginacion.items, 
                           paginacion=paginacion,
                           ultimo_evento=ultimo_evento)

@bp.route('/deshacer_accion', methods=['POST'])
@login_required
def deshacer_accion():
    if current_user.tipo_usuario == 'estudiante':
        return redirect(url_for('main.index'))
    
    # Sincronizamos la BD con la Pila
    logs_db = HistorialAccion.query.order_by(HistorialAccion.fecha.asc()).all()
    pila = Pila()
    for log in logs_db:
        pila.apilar(log)
    
    if not pila.esta_vacia():
        # LIFO: El último en entrar es el primero en salir
        ultimo_log = pila.desapilar() 
        # Eliminamos de la base de datos para "deshacer" el registro
        db.session.delete(ultimo_log)
        db.session.commit()
        flash(f'Acción deshecha (PILA LIFO): {ultimo_log.accion}', 'warning')
    else:
        flash('No hay acciones para deshacer.', 'info')
        
    return redirect(url_for('tramites.bitacora'))


@bp.route('/exportar_csv')
@login_required
def exportar_csv():
    if current_user.tipo_usuario == 'estudiante':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))
    import csv, io
    logs = HistorialAccion.query.order_by(HistorialAccion.fecha.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Fecha', 'Usuario_ID', 'Accion'])
    for log in logs:
        writer.writerow([log.id, log.fecha.strftime('%Y-%m-%d %H:%M:%S'), log.usuario_id or 'Sistema', log.accion])
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=bitacora_smartcampus.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@bp.route('/cambiar_estado/<int:tramite_id>', methods=['POST'])
@login_required
def cambiar_estado(tramite_id):
    if current_user.tipo_usuario == 'estudiante':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))
    tramite = Tramite.query.get_or_404(tramite_id)
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ESTADOS_VALIDOS:
        tramite.estado = nuevo_estado
        db.session.add(HistorialAccion(
            usuario_id=current_user.id,
            accion=f"Cambió estado del trámite #{tramite.id} a '{nuevo_estado}'"
        ))
        db.session.commit()
        flash('Estado actualizado correctamente.', 'success')
    return redirect(url_for('tramites.historial'))
