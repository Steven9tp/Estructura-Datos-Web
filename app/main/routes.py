from flask import render_template, redirect, url_for, flash
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
