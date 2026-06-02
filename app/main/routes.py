from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    from app.models import Usuario, Turno, Tramite
    stats = {
        'usuarios': Usuario.query.filter_by(activo=True).count(),
        'turnos_hoy': Turno.query.filter(
            db.func.date(Turno.fecha_emision) == date.today()
        ).count(),
        'turnos_espera': Turno.query.filter_by(estado='en_espera').count(),
        'tramites_pendientes': Tramite.query.filter(
            Tramite.estado.in_(['iniciado', 'en_revision'])
        ).count(),
    }
    return render_template('index.html', stats=stats)

@bp.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

@bp.route('/admin_panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.tipo_usuario != 'admin':
        flash('Acceso denegado. Solo administradores pueden ingresar al panel.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models import Usuario, Turno, Tramite
    
    # Manejar cambios de rol o estado de usuario
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id', type=int)
        
        if action == 'cambiar_rol' and user_id:
            nuevo_rol = request.form.get('nuevo_rol')
            if nuevo_rol in ['estudiante', 'empleado', 'admin']:
                usuario = db.session.get(Usuario, user_id)
                if usuario:
                    usuario.tipo_usuario = nuevo_rol
                    db.session.commit()
                    flash(f'Rol del usuario {usuario.nombres} actualizado a {nuevo_rol}.', 'success')
        
        elif action == 'toggle_activo' and user_id:
            usuario = db.session.get(Usuario, user_id)
            if usuario:
                if usuario.id == current_user.id:
                    flash('No puedes desactivarte a ti mismo.', 'warning')
                else:
                    usuario.activo = not usuario.activo
                    db.session.commit()
                    estado = "activado" if usuario.activo else "desactivado"
                    flash(f'Usuario {usuario.nombres} {estado} correctamente.', 'success')
                    
        return redirect(url_for('main.admin_panel'))
    
    usuarios = Usuario.query.all()
    stats = {
        'total_usuarios': Usuario.query.count(),
        'total_estudiantes': Usuario.query.filter_by(tipo_usuario='estudiante').count(),
        'total_personal': Usuario.query.filter_by(tipo_usuario='empleado').count(),
        'total_admins': Usuario.query.filter_by(tipo_usuario='admin').count(),
        'turnos_atendidos': Turno.query.filter_by(estado='atendido').count(),
        'turnos_espera': Turno.query.filter_by(estado='en_espera').count(),
    }
    
    return render_template('admin/admin_panel.html', usuarios=usuarios, stats=stats)
