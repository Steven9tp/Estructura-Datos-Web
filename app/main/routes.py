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
    import os
    import time
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    form = EditarPerfilForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.nombre      = form.nombre.data
        current_user.apellido    = form.apellido.data or ''
        current_user.genero      = form.genero.data or ''
        current_user.carrera     = form.carrera.data or ''
        current_user.facultad    = form.facultad.data or ''
        current_user.semestre    = form.semestre.data or ''
        current_user.telefono    = form.telefono.data or ''
        current_user.contacto_emergencia_nombre = form.contacto_emergencia_nombre.data or ''
        current_user.contacto_emergencia_telefono = form.contacto_emergencia_telefono.data or ''
        current_user.cedula      = form.cedula.data or ''
        current_user.tipo_sangre = form.tipo_sangre.data or ''
        current_user.fecha_nacimiento = form.fecha_nacimiento.data
        current_user.direccion   = form.direccion.data or ''
        current_user.calles_secundarias = form.calles_secundarias.data or ''
        
        if form.direccion_lat.data and form.direccion_lng.data:
            try:
                current_user.direccion_lat = float(form.direccion_lat.data)
                current_user.direccion_lng = float(form.direccion_lng.data)
            except ValueError:
                pass
        
        # Procesar foto si se sube
        f = form.foto_perfil.data
        if f and getattr(f, 'filename', ''):
            filename = secure_filename(f.filename)
            unique_name = f"{current_user.id}_{int(time.time())}_{filename}"
            # Asegurar que el directorio exista en la carpeta estática del frontend
            upload_folder = os.path.join(current_app.static_folder, 'img', 'perfiles')
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, unique_name)
            f.save(filepath)
            
            # Guardar la ruta relativa para el navegador
            current_user.foto_url = f'img/perfiles/{unique_name}'
            
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('main.perfil'))
        
    return render_template('editar_perfil.html', form=form)

