from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Viaje


@bp.route('/')
@bp.route('/index')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    viajes_recientes = (
        Viaje.query
        .filter_by(estado='abierto')
        .order_by(Viaje.fecha_hora.asc())
        .limit(6)
        .all()
    )
    return render_template('index.html', viajes_recientes=viajes_recientes)


@bp.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')


@bp.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    from app.forms import EditarPerfilForm
    form = EditarPerfilForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nombre      = form.nombre.data
        current_user.apellido    = form.apellido.data or ''
        current_user.genero      = form.genero.data or ''
        current_user.carrera     = form.carrera.data
        current_user.telefono    = form.telefono.data
        current_user.fecha_nacimiento = form.fecha_nacimiento.data
        current_user.zona_barrio = form.zona_barrio.data
        current_user.direccion   = form.direccion.data or ''
        current_user.foto_url    = form.foto_url.data
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('main.perfil'))
    return render_template('editar_perfil.html', form=form)
