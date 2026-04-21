from flask import render_template, url_for, flash, redirect, request, session # <--- SE AGREGÓ 'session'
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario, Viaje, Reserva 
from app.auth.forms import RegistroForm, LoginForm, PublicarViajeForm
from app.main import main_bp

# --- RUTA PARA CAMBIAR DE ROL (DINÁMICO) ---
@main_bp.route("/cambiar_rol/<nuevo_rol>")
@login_required
def cambiar_rol(nuevo_rol):
    # Guardamos el rol en la sesión del navegador
    session['rol_activo'] = nuevo_rol
    if nuevo_rol == 'conductor':
        flash('Has cambiado al Modo Conductor. Ahora puedes gestionar tus rutas.', 'primary')
        return redirect(url_for('main.mis_viajes'))
    else:
        flash('Has cambiado al Modo Pasajero. ¡Buen viaje!', 'danger')
        return redirect(url_for('main.buscar_viaje'))

# --- RUTA DE INICIO ---
@main_bp.route("/")
@main_bp.route("/index")
def index():
    return render_template('index.html', title='Inicio')

# --- RUTA DE LOGIN ---
@main_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            # Al iniciar sesión, ponemos por defecto el modo pasajero
            session['rol_activo'] = 'pasajero'
            flash(f'¡Bienvenido de nuevo, {user.nombre}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Error al iniciar sesión. Revisa tus credenciales.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

# --- RUTA DE REGISTRO ---
@main_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistroForm()
    if form.validate_on_submit():
        nuevo_usuario = Usuario(nombre=form.nombre.data, email=form.email.data)
        nuevo_usuario.set_password(form.password.data)
        db.session.add(nuevo_usuario)
        db.session.commit()
        login_user(nuevo_usuario)
        session['rol_activo'] = 'pasajero'
        flash('¡Cuenta creada con éxito!', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html', title='Registro', form=form)

# --- RUTA PARA BUSCAR VIAJES (FILTRADA) ---
@main_bp.route("/buscar")
@login_required
def buscar_viaje():
    viajes = Viaje.query.filter_by(activo=True).all()
    return render_template('buscar.html', title='Viajes Disponibles', viajes=viajes)

# --- RUTA PARA PUBLICAR VIAJE ---
@main_bp.route("/publicar", methods=['GET', 'POST'])
@login_required
def publicar_viaje():
    form = PublicarViajeForm()
    if form.validate_on_submit():
        nuevo_viaje = Viaje(
            origen=form.origen.data,
            destino=form.destino.data,
            hora_salida=form.hora_salida.data,
            asientos_disponibles=form.asientos.data,
            precio=form.precio.data,
            conductor=current_user
        )
        db.session.add(nuevo_viaje)
        db.session.commit()
        flash('¡Tu viaje ha sido publicado con éxito!', 'success')
        return redirect(url_for('main.mis_viajes'))
    return render_template('publicar.html', title='Publicar Viaje', form=form)

# --- RUTA PARA RESERVAR ---
@main_bp.route("/reservar/<int:viaje_id>", methods=['POST'])
@login_required
def reservar(viaje_id):
    viaje = Viaje.query.get_or_404(viaje_id)
    if viaje.asientos_disponibles > 0:
        if viaje.conductor_id != current_user.id:
            viaje.asientos_disponibles -= 1
            nueva_reserva = Reserva(usuario_id=current_user.id, viaje_id=viaje.id)
            db.session.add(nueva_reserva)
            db.session.commit()
            flash('¡Asiento reservado con éxito!', 'success')
        else:
            flash('No puedes reservar tu propio viaje.', 'warning')
    else:
        flash('Lo sentimos, ya no hay asientos disponibles.', 'danger')
    return redirect(url_for('main.buscar_viaje'))

# --- RUTA MIS RESERVAS ---
@main_bp.route("/mis_reservas")
@login_required
def mis_reservas():
    reservas = current_user.mis_reservas
    return render_template('mis_reservas.html', title='Mis Reservas', reservas=reservas)

# --- RUTA MIS VIAJES (CONDUCTOR) ---
@main_bp.route("/mis_viajes")
@login_required
def mis_viajes():
    viajes = Viaje.query.filter_by(conductor_id=current_user.id).all()
    return render_template('mis_viajes.html', title='Mis Viajes Publicados', viajes=viajes)

# --- FINALIZAR VIAJE ---
@main_bp.route("/finalizar_viaje/<int:viaje_id>", methods=['POST'])
@login_required
def finalizar_viaje(viaje_id):
    viaje = Viaje.query.get_or_404(viaje_id)
    if viaje.conductor_id == current_user.id:
        viaje.activo = False
        db.session.commit()
        flash('El viaje ha sido marcado como completado.', 'success')
    return redirect(url_for('main.mis_viajes'))

# --- ELIMINAR VIAJE ---
@main_bp.route("/eliminar_viaje/<int:viaje_id>", methods=['POST'])
@login_required
def eliminar_viaje(viaje_id):
    viaje = Viaje.query.get_or_404(viaje_id)
    if viaje.conductor_id == current_user.id:
        Reserva.query.filter_by(viaje_id=viaje.id).delete()
        db.session.delete(viaje)
        db.session.commit()
        flash('Viaje eliminado correctamente.', 'info')
    return redirect(url_for('main.mis_viajes'))

# --- PERFIL ---
@main_bp.route("/perfil")
@login_required
def perfil():
    num_viajes = Viaje.query.filter_by(conductor_id=current_user.id).count()
    num_reservas = len(current_user.mis_reservas)
    return render_template('perfil.html', title='Mi Perfil', num_viajes=num_viajes, num_reservas=num_reservas)

# --- LOGOUT ---
@main_bp.route("/logout")
def logout():
    session.pop('rol_activo', None) # Limpiamos el rol al salir
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('main.index'))
