from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import Usuario, Viaje, Reporte


def solo_admin(f):
    """Decorador para rutas solo de admin"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@bp.route('/dashboard')
@login_required
@solo_admin
def dashboard():
    total_usuarios = Usuario.query.count()
    total_viajes = Viaje.query.count()
    reportes_pendientes = Reporte.query.filter_by(estado='pendiente').count()
    viajes_activos = Viaje.query.filter_by(estado='abierto').count()
    return render_template('admin/dashboard.html', title='Panel Admin',
                           total_usuarios=total_usuarios,
                           total_viajes=total_viajes,
                           reportes_pendientes=reportes_pendientes,
                           viajes_activos=viajes_activos)


@bp.route('/reportes')
@login_required
@solo_admin
def reportes():
    pendientes = Reporte.query.filter_by(estado='pendiente').order_by(
        Reporte.fecha.desc()).all()
    revisados = Reporte.query.filter(
        Reporte.estado != 'pendiente'
    ).order_by(Reporte.fecha.desc()).limit(20).all()
    return render_template('admin/reportes.html', title='Gestión de Reportes',
                           pendientes=pendientes, revisados=revisados)


@bp.route('/reportes/<int:reporte_id>/resolver', methods=['POST'])
@login_required
@solo_admin
def resolver_reporte(reporte_id):
    from flask import request
    reporte = db.get_or_404(Reporte, reporte_id)
    accion = request.form.get('accion', 'Revisado sin acción')
    tipo = request.form.get('tipo_sancion', 'ninguna')  # RF11: tipo diferenciado
    reporte.tomar_accion(accion, tipo=tipo)  # solo modifica, no hace commit

    # Si la sancion es suspension, suspender al usuario reportado en la misma transaccion
    if tipo == 'suspension':
        reportado = db.session.get(Usuario, reporte.reportado_id)
        if reportado and not reportado.es_admin:
            reportado.esta_activo = False
            db.session.commit()  # commit unico que incluye reporte + suspension
            flash(f'Usuario {reportado.nombre} suspendido y reporte resuelto.', 'success')
        else:
            db.session.commit()
            flash('Reporte resuelto correctamente.', 'success')
    else:
        db.session.commit()  # commit unico: solo el reporte
        flash('Reporte resuelto correctamente.', 'success')
    return redirect(url_for('admin.reportes'))


@bp.route('/usuarios')
@login_required
@solo_admin
def usuarios():
    lista = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    return render_template('admin/usuarios.html', title='Gestión de Usuarios',
                           usuarios=lista)


@bp.route('/usuarios/<int:usuario_id>/suspender', methods=['POST'])
@login_required
@solo_admin
def suspender_usuario(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.es_admin:
        flash('No puedes suspender a un administrador.', 'danger')
        return redirect(url_for('admin.usuarios'))
    usuario.esta_activo = not usuario.esta_activo
    db.session.commit()
    estado = 'activado' if usuario.esta_activo else 'suspendido'
    flash(f'Usuario {usuario.nombre} {estado} correctamente.', 'success')
    return redirect(url_for('admin.usuarios'))


@bp.route('/estadisticas')
@login_required
@solo_admin
def estadisticas():
    from app.models import Solicitud, Calificacion
    stats = {
        'usuarios': Usuario.query.count(),
        'usuarios_activos': Usuario.query.filter_by(esta_activo=True).count(),
        'viajes_totales': Viaje.query.count(),
        'viajes_finalizados': Viaje.query.filter_by(estado='finalizado').count(),
        'solicitudes_aceptadas': Solicitud.query.filter_by(estado='aceptada').count(),
        'calificaciones': Calificacion.query.count(),
        'reportes_pendientes': Reporte.query.filter_by(estado='pendiente').count(),
    }
    return render_template('admin/estadisticas.html', title='Estadísticas', stats=stats)