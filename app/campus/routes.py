from flask import render_template, request, flash, make_response
from flask_login import login_required
from app import db
from app.campus import bp
from app.models import PuntoRuta, ConexionRuta
from app.estructuras.basicas import Grafo

# Posiciones en píxeles ajustadas para el mapa OSM (800x800)
POSICIONES_SVG = {
    'Aulas de Nivelación':                (430, 140),
    'FCHE (Ciencias Humanas)':            (280, 200),
    'Edificio Académico':                 (600, 260),
    'Centro de Idiomas':                  (610, 320),
    'FISEI (Sistemas/Industrial)':        (480, 270),
    'Jurisprudencia y Sociales':          (420, 360),
    'Ciencias Administrativas':           (260, 360),
    'Comedor Universitario':              (430, 440),
    'FCA (Contabilidad y Auditoría)':     (380, 520),
    'FICM (Civil/Mecánica)':              (530, 510),
    'Coliseo Universidad':                (480, 680),
    'Complejo Acuático UTA':              (500, 750),
    'FEUE':                               (410, 780),
    'Servicio Médico':                    (380, 840),
    'Canchas y Cultura Física':           (680, 830),
}

def inicializar_datos_campus():
    # Solo inicializar si la base de datos está vacía para no desfasar los IDs
    if PuntoRuta.query.count() > 0:
        return
        
    # FORZAMOS la recreación limpia de la base de datos si está vacía
    # por conexiones fantasma o desajuste de IDs.
    ConexionRuta.query.delete()
    PuntoRuta.query.delete()
    db.session.commit()

    puntos_obj = {}
    for nombre, (x, y) in POSICIONES_SVG.items():
        p = PuntoRuta(nombre=nombre, descripcion=f'Campus Huachi')
        db.session.add(p)
        puntos_obj[nombre] = p
    
    db.session.commit()
    
    # Conexiones exclusivas basadas en el croquis OSM
    conexiones = [
        # Zona Norte
        ConexionRuta(punto_origen_id=puntos_obj['Aulas de Nivelación'].id, punto_destino_id=puntos_obj['FCHE (Ciencias Humanas)'].id, distancia_metros=120),
        ConexionRuta(punto_origen_id=puntos_obj['Aulas de Nivelación'].id, punto_destino_id=puntos_obj['FISEI (Sistemas/Industrial)'].id, distancia_metros=90),
        ConexionRuta(punto_origen_id=puntos_obj['Edificio Académico'].id, punto_destino_id=puntos_obj['Centro de Idiomas'].id, distancia_metros=40),
        ConexionRuta(punto_origen_id=puntos_obj['FISEI (Sistemas/Industrial)'].id, punto_destino_id=puntos_obj['Edificio Académico'].id, distancia_metros=80),
        
        # Conexiones FCHE y FCA
        ConexionRuta(punto_origen_id=puntos_obj['FCHE (Ciencias Humanas)'].id, punto_destino_id=puntos_obj['Ciencias Administrativas'].id, distancia_metros=100),
        ConexionRuta(punto_origen_id=puntos_obj['Ciencias Administrativas'].id, punto_destino_id=puntos_obj['Jurisprudencia y Sociales'].id, distancia_metros=80),
        
        # Zona Central (Jurisprudencia y Comedor)
        ConexionRuta(punto_origen_id=puntos_obj['FISEI (Sistemas/Industrial)'].id, punto_destino_id=puntos_obj['Jurisprudencia y Sociales'].id, distancia_metros=50),
        ConexionRuta(punto_origen_id=puntos_obj['Jurisprudencia y Sociales'].id, punto_destino_id=puntos_obj['Comedor Universitario'].id, distancia_metros=45),
        ConexionRuta(punto_origen_id=puntos_obj['Centro de Idiomas'].id, punto_destino_id=puntos_obj['FICM (Civil/Mecánica)'].id, distancia_metros=160),
        
        # Comedor hacia Facultades Sur
        ConexionRuta(punto_origen_id=puntos_obj['Ciencias Administrativas'].id, punto_destino_id=puntos_obj['FCA (Contabilidad y Auditoría)'].id, distancia_metros=130),
        ConexionRuta(punto_origen_id=puntos_obj['Comedor Universitario'].id, punto_destino_id=puntos_obj['FCA (Contabilidad y Auditoría)'].id, distancia_metros=50),
        ConexionRuta(punto_origen_id=puntos_obj['Comedor Universitario'].id, punto_destino_id=puntos_obj['FICM (Civil/Mecánica)'].id, distancia_metros=60),
        
        # Zona Sur (Deportiva y Servicios)
        ConexionRuta(punto_origen_id=puntos_obj['FICM (Civil/Mecánica)'].id, punto_destino_id=puntos_obj['Coliseo Universidad'].id, distancia_metros=110),
        ConexionRuta(punto_origen_id=puntos_obj['FCA (Contabilidad y Auditoría)'].id, punto_destino_id=puntos_obj['Coliseo Universidad'].id, distancia_metros=120),
        ConexionRuta(punto_origen_id=puntos_obj['Coliseo Universidad'].id, punto_destino_id=puntos_obj['Complejo Acuático UTA'].id, distancia_metros=40),
        ConexionRuta(punto_origen_id=puntos_obj['Coliseo Universidad'].id, punto_destino_id=puntos_obj['Canchas y Cultura Física'].id, distancia_metros=150),
        ConexionRuta(punto_origen_id=puntos_obj['Complejo Acuático UTA'].id, punto_destino_id=puntos_obj['FEUE'].id, distancia_metros=35),
        ConexionRuta(punto_origen_id=puntos_obj['FEUE'].id, punto_destino_id=puntos_obj['Servicio Médico'].id, distancia_metros=45),
    ]
    db.session.add_all(conexiones)
    db.session.commit()

def construir_grafo():
    grafo = Grafo()
    for punto in PuntoRuta.query.all():
        grafo.agregar_nodo(punto.id)
    for conexion in ConexionRuta.query.all():
        grafo.agregar_arista(conexion.punto_origen_id, conexion.punto_destino_id, conexion.distancia_metros)
    return grafo

@bp.route('/rutas', methods=['GET', 'POST'])
@login_required
def rutas():
    inicializar_datos_campus()
    puntos = PuntoRuta.query.all()
    conexiones = ConexionRuta.query.all()

    # Diccionario id->punto
    puntos_dict = {p.id: p for p in puntos}
    
    # Posiciones SVG por ID
    pos = {}
    for p in puntos:
        pos[p.id] = POSICIONES_SVG.get(p.nombre, (300, 170))

    ruta_calculada = []
    distancia_total = 0
    origen_sel = None
    destino_sel = None

    if request.method == 'POST':
        origen_id  = int(request.form.get('origen'))
        destino_id = int(request.form.get('destino'))
        origen_sel  = origen_id
        destino_sel = destino_id

        if origen_id == destino_id:
            flash('El origen y el destino deben ser diferentes.', 'warning')
        else:
            grafo = construir_grafo()
            ruta_ids, distancia_total = grafo.dijkstra(origen_id, destino_id)
            if ruta_ids:
                ruta_calculada = [puntos_dict[r].nombre for r in ruta_ids if r in puntos_dict]
                flash(f'Ruta óptima encontrada: {distancia_total:.0f} metros.', 'success')
                from app.models import HistorialAccion
                from flask_login import current_user
                log = HistorialAccion(
                    usuario_id=current_user.id,
                    accion=f"Calculó ruta: {puntos_dict[origen_id].nombre} → {puntos_dict[destino_id].nombre} ({distancia_total:.0f}m)"
                )
                db.session.add(log)
                db.session.commit()
            else:
                flash('No se encontró una ruta entre esos puntos.', 'danger')

    return render_template(
        'campus/mapa.html',
        puntos=puntos,
        conexiones=conexiones,
        puntos_dict=puntos_dict,
        pos=pos,
        ruta=ruta_calculada,
        distancia=distancia_total,
        origen_sel=origen_sel,
        destino_sel=destino_sel,
    )
