from flask import render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app import db
from app.reportes import bp
from app.models import Usuario, Turno, Tramite, Dependencia, PuntoRuta, ConexionRuta, HistorialAccion
from app.organizacion.routes import construir_arbol_desde_db
from app.campus.routes import construir_grafo
from app.atencion.routes import sincronizar_colas, colas
from datetime import datetime, timedelta

@bp.route('/dashboard')
@login_required
def dashboard():
    # ── 1. Seguridad: Solo empleado o administrador pueden ver reportes detallados ──
    if current_user.tipo_usuario == 'estudiante':
        flash('Acceso denegado. Solo personal académico o administrativo puede ingresar a Reportes.', 'danger')
        return redirect(url_for('main.index'))

    # Sincronizamos las colas en memoria para que la información sea exacta
    sincronizar_colas()

    # ── 2. Estadísticas Generales (KPIs) ──
    total_usuarios = Usuario.query.count()
    estudiantes = Usuario.query.filter_by(tipo_usuario='estudiante').count()
    empleados = Usuario.query.filter_by(tipo_usuario='empleado').count()
    admins = Usuario.query.filter_by(tipo_usuario='admin').count()

    total_turnos = Turno.query.count()
    turnos_espera = Turno.query.filter_by(estado='en_espera').count()
    turnos_atendidos = Turno.query.filter_by(estado='atendido').count()
    turnos_cancelados = Turno.query.filter_by(estado='cancelado').count()

    total_tramites = Tramite.query.count()
    tramites_iniciados = Tramite.query.filter_by(estado='iniciado').count()
    tramites_revision = Tramite.query.filter_by(estado='en_revision').count()
    tramites_aprobados = Tramite.query.filter_by(estado='aprobado').count()
    tramites_rechazados = Tramite.query.filter_by(estado='rechazado').count()

    # ── 3. Trazabilidad de Estructuras de Datos Propias (Clave Académica) ──
    # A. Árbol N-Ario (Organigrama)
    arbol = construir_arbol_desde_db()
    altura_arbol = arbol.altura() if arbol else 0
    nodos_arbol = arbol.contar_nodos() if arbol else 0

    # B. Grafo (Mapa de Rutas)
    grafo = construir_grafo()
    vertices_grafo = grafo.total_nodos() if grafo else 0
    aristas_grafo = grafo.total_aristas() if grafo else 0

    # C. Colas FIFO (Ventanilla Virtual)
    # Contamos cuántas colas activas en memoria tienen elementos en espera
    colas_activas = 0
    total_elementos_en_colas = 0
    detalles_colas = []
    
    all_dependencias = Dependencia.query.all()
    for dep in all_dependencias:
        dep_cola = colas.get(dep.id)
        elementos = len(dep_cola) if dep_cola else 0
        if elementos > 0:
            colas_activas += 1
            total_elementos_en_colas += elementos
        detalles_colas.append({
            'dependencia': dep.nombre,
            'en_cola': elementos,
            'tiempo_estimado': elementos * 5
        })

    # D. Pila LIFO (Historial de Bitácora)
    total_logs = HistorialAccion.query.count()

    # ── 4. Distribución de Trámites por Tipo ──
    dist_tramites = db.session.query(
        Tramite.tipo_tramite, db.func.count(Tramite.id)
    ).group_by(Tramite.tipo_tramite).all()
    
    tipos_traducidos = {
        'certificado_matricula': 'Certificado de Matrícula',
        'solicitud_especie': 'Solicitud de Especie Valorada',
        'justificacion_falta': 'Justificación de Falta',
        'retiro_asignatura': 'Retiro de Asignatura'
    }
    
    reporte_tramites = []
    for tipo, cant in dist_tramites:
        nombre_legible = tipos_traducidos.get(tipo, tipo)
        reporte_tramites.append({'tipo': nombre_legible, 'cantidad': cant})

    # ── 5. Rendimiento de Atención (Tiempos de Atención) ──
    # Promedio del tiempo transcurrido entre la emisión del turno y la atención
    turnos_con_atencion = Turno.query.filter(Turno.estado == 'atendido', Turno.fecha_atencion != None).all()
    tiempos_espera = []
    for t in turnos_con_atencion:
        delta = t.fecha_atencion - t.fecha_emision
        tiempos_espera.append(delta.total_seconds() / 60.0) # en minutos
    
    promedio_espera = sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0.0

    return render_template(
        'reportes/dashboard.html',
        total_usuarios=total_usuarios,
        estudiantes=estudiantes,
        empleados=empleados,
        admins=admins,
        total_turnos=total_turnos,
        turnos_espera=turnos_espera,
        turnos_atendidos=turnos_atendidos,
        turnos_cancelados=turnos_cancelados,
        total_tramites=total_tramites,
        tramites_iniciados=tramites_iniciados,
        tramites_revision=tramites_revision,
        tramites_aprobados=tramites_aprobados,
        tramites_rechazados=tramites_rechazados,
        altura_arbol=altura_arbol,
        nodos_arbol=nodos_arbol,
        vertices_grafo=vertices_grafo,
        aristas_grafo=aristas_grafo,
        colas_activas=colas_activas,
        total_elementos_en_colas=total_elementos_en_colas,
        detalles_colas=detalles_colas,
        total_logs=total_logs,
        reporte_tramites=reporte_tramites,
        promedio_espera=round(promedio_espera, 1)
    )

@bp.route('/exportar/<string:tipo>', methods=['GET'])
@login_required
def exportar(tipo):
    if current_user.tipo_usuario == 'estudiante':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))

    import csv
    import io

    if tipo == 'turnos':
        turnos = Turno.query.order_by(Turno.fecha_emision.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Código de Turno', 'Usuario', 'Dependencia', 'Estado', 'Fecha Emisión', 'Fecha Atención'])
        for t in turnos:
            writer.writerow([
                t.id, 
                t.codigo_turno, 
                t.usuario.nombre_completo if t.usuario else 'N/A', 
                t.dependencia_lugar.nombre if t.dependencia_lugar else 'N/A', 
                t.estado, 
                t.fecha_emision.strftime('%Y-%m-%d %H:%M:%S') if t.fecha_emision else 'N/A',
                t.fecha_atencion.strftime('%Y-%m-%d %H:%M:%S') if t.fecha_atencion else 'N/A'
            ])
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_turnos.csv'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response

    elif tipo == 'tramites':
        tramites = Tramite.query.order_by(Tramite.fecha_inicio.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Solicitante', 'Tipo Trámite', 'Estado', 'Fecha Inicio', 'Fecha Actualización', 'Observaciones'])
        tipos_traducidos = {
            'certificado_matricula': 'Certificado de Matrícula',
            'solicitud_especie': 'Solicitud de Especie Valorada',
            'justificacion_falta': 'Justificación de Falta',
            'retiro_asignatura': 'Retiro de Asignatura'
        }
        for tr in tramites:
            writer.writerow([
                tr.id, 
                tr.solicitante.nombre_completo if tr.solicitante else 'N/A', 
                tipos_traducidos.get(tr.tipo_tramite, tr.tipo_tramite), 
                tr.estado, 
                tr.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S') if tr.fecha_inicio else 'N/A',
                tr.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if tr.fecha_actualizacion else 'N/A',
                tr.observaciones or ''
            ])
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=reporte_tramites.csv'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response

    flash('Tipo de reporte no válido.', 'warning')
    return redirect(url_for('reportes.dashboard'))
