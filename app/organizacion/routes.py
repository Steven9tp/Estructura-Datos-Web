from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.organizacion import bp
from app.models import Dependencia, CategoriaDocumento, Documento
from app.estructuras.basicas import NodoArbol, ArbolNArio

def construir_arbol_desde_db():
    """Recorre la DB y construye la estructura de Árbol N-Ario en memoria."""
    dependencias = Dependencia.query.all()
    if not dependencias:
        return None

    arbol = ArbolNArio()

    # 1. Encontrar la raíz (la que no tiene padre)
    raiz_db = next((d for d in dependencias if d.dependencia_padre_id is None), None)
    if not raiz_db:
        return None

    nodo_raiz = NodoArbol(dato=raiz_db.nombre, id_ref=raiz_db.id)
    arbol.establecer_raiz(nodo_raiz)

    # 2. Función recursiva para poblar hijos
    def poblar_hijos(nodo_actual):
        hijos_db = [d for d in dependencias if d.dependencia_padre_id == nodo_actual.id_ref]
        for h in hijos_db:
            nuevo_nodo = NodoArbol(dato=h.nombre, id_ref=h.id)
            nodo_actual.agregar_hijo(nuevo_nodo)
            poblar_hijos(nuevo_nodo)

    poblar_hijos(nodo_raiz)
    return arbol

def seed_dependencias():
    """Inserta datos semilla con las 10 facultades reales de la UTA."""
    rectorado = Dependencia(nombre='Rectorado UTA')
    db.session.add(rectorado)
    db.session.commit()

    # ── 10 Facultades oficiales de la UTA (fuente: uta.edu.ec) ──────────────
    fisei  = Dependencia(nombre='Facultad de Ingeniería en Sistemas, Electrónica e Industrial (FISEI)', dependencia_padre_id=rectorado.id)
    fca    = Dependencia(nombre='Facultad de Ciencias Administrativas (FCA)',                           dependencia_padre_id=rectorado.id)
    fcial  = Dependencia(nombre='Facultad de Ciencia e Ingeniería en Alimentos y Biotecnología (FCIAL)',dependencia_padre_id=rectorado.id)
    fcag   = Dependencia(nombre='Facultad de Ciencias Agropecuarias (FCAG)',                            dependencia_padre_id=rectorado.id)
    ficm   = Dependencia(nombre='Facultad de Ingeniería Civil y Mecánica (FICM)',                       dependencia_padre_id=rectorado.id)
    fcs    = Dependencia(nombre='Facultad de Ciencias de la Salud (FCS)',                               dependencia_padre_id=rectorado.id)
    fda    = Dependencia(nombre='Facultad de Diseño y Arquitectura (FDA)',                              dependencia_padre_id=rectorado.id)
    fcaud  = Dependencia(nombre='Facultad de Contabilidad y Auditoría (FCAUD)',                         dependencia_padre_id=rectorado.id)
    fche   = Dependencia(nombre='Facultad de Ciencias Humanas y de la Educación (FCHE)',                dependencia_padre_id=rectorado.id)
    fjcs   = Dependencia(nombre='Facultad de Jurisprudencia y Ciencias Sociales (FJCS)',                dependencia_padre_id=rectorado.id)
    db.session.add_all([fisei, fca, fcial, fcag, ficm, fcs, fda, fcaud, fche, fjcs])
    db.session.commit()

    # ── Carreras por facultad ────────────────────────────────────────────────
    # FISEI
    db.session.add_all([
        Dependencia(nombre='Ingeniería en Software',                    dependencia_padre_id=fisei.id),
        Dependencia(nombre='Ingeniería en Sistemas Computacionales',    dependencia_padre_id=fisei.id),
        Dependencia(nombre='Ingeniería en Electrónica y Comunicaciones',dependencia_padre_id=fisei.id),
        Dependencia(nombre='Ingeniería Industrial',                     dependencia_padre_id=fisei.id),
    ])
    # FCA
    db.session.add_all([
        Dependencia(nombre='Administración de Empresas',  dependencia_padre_id=fca.id),
        Dependencia(nombre='Marketing y Gestión de Negocios', dependencia_padre_id=fca.id),
    ])
    # FCIAL
    db.session.add_all([
        Dependencia(nombre='Ingeniería en Alimentos',  dependencia_padre_id=fcial.id),
        Dependencia(nombre='Biotecnología',            dependencia_padre_id=fcial.id),
    ])
    # FCAG
    db.session.add_all([
        Dependencia(nombre='Ingeniería Agronómica',   dependencia_padre_id=fcag.id),
        Dependencia(nombre='Medicina Veterinaria',    dependencia_padre_id=fcag.id),
    ])
    # FICM
    db.session.add_all([
        Dependencia(nombre='Ingeniería Civil',    dependencia_padre_id=ficm.id),
        Dependencia(nombre='Ingeniería Mecánica', dependencia_padre_id=ficm.id),
    ])
    # FCS
    db.session.add_all([
        Dependencia(nombre='Medicina',          dependencia_padre_id=fcs.id),
        Dependencia(nombre='Enfermería',        dependencia_padre_id=fcs.id),
        Dependencia(nombre='Laboratorio Clínico', dependencia_padre_id=fcs.id),
        Dependencia(nombre='Fisioterapia',      dependencia_padre_id=fcs.id),
    ])
    # FDA
    db.session.add_all([
        Dependencia(nombre='Diseño Gráfico Publicitario', dependencia_padre_id=fda.id),
        Dependencia(nombre='Arquitectura',                dependencia_padre_id=fda.id),
    ])
    # FCAUD
    db.session.add_all([
        Dependencia(nombre='Contabilidad y Auditoría CPA', dependencia_padre_id=fcaud.id),
    ])
    # FCHE
    db.session.add_all([
        Dependencia(nombre='Educación Básica',       dependencia_padre_id=fche.id),
        Dependencia(nombre='Comunicación Social',    dependencia_padre_id=fche.id),
        Dependencia(nombre='Psicopedagogía',         dependencia_padre_id=fche.id),
    ])
    # FJCS
    db.session.add_all([
        Dependencia(nombre='Derecho',                dependencia_padre_id=fjcs.id),
        Dependencia(nombre='Trabajo Social',         dependencia_padre_id=fjcs.id),
    ])
    db.session.commit()

    # ── Categorías de documentos ─────────────────────────────────────────────
    cats = ['Reglamentos', 'Normativas Académicas', 'Formularios', 'Circulares']
    for c in cats:
        db.session.add(CategoriaDocumento(nombre=c))
    db.session.commit()


@bp.route('/organigrama')
@login_required
def organigrama():
    arbol = construir_arbol_desde_db()
    if not arbol:
        seed_dependencias()
        arbol = construir_arbol_desde_db()

    # Estadísticas del árbol
    stats = {
        'altura': arbol.altura(),
        'nodos': arbol.contar_nodos()
    }
    return render_template('organizacion/arbol.html', raiz=arbol.raiz, stats=stats)


# ─── RF7: Gestión de Documentos ────────────────────────────────

@bp.route('/documentos')
@login_required
def documentos():
    categorias = CategoriaDocumento.query.all()
    cat_sel = request.args.get('cat', None, type=int)
    if cat_sel:
        docs = Documento.query.filter_by(categoria_id=cat_sel).order_by(Documento.fecha_subida.desc()).all()
    else:
        docs = Documento.query.order_by(Documento.fecha_subida.desc()).all()
    return render_template('organizacion/documentos.html', categorias=categorias, docs=docs, cat_sel=cat_sel)


@bp.route('/documentos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_documento():
    if current_user.tipo_usuario == 'estudiante':
        flash('Solo empleados pueden subir documentos.', 'danger')
        return redirect(url_for('organizacion.documentos'))

    categorias = CategoriaDocumento.query.all()
    if not categorias:
        seed_dependencias()
        categorias = CategoriaDocumento.query.all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        categoria_id = request.form.get('categoria_id', type=int)
        ruta = request.form.get('ruta_archivo', '').strip()

        if not titulo or not categoria_id:
            flash('El título y la categoría son obligatorios.', 'danger')
        else:
            doc = Documento(titulo=titulo, categoria_id=categoria_id, ruta_archivo=ruta or None)
            db.session.add(doc)

            from app.models import HistorialAccion
            log = HistorialAccion(usuario_id=current_user.id, accion=f'Publicó documento: "{titulo}"')
            db.session.add(log)
            db.session.commit()
            flash(f'Documento "{titulo}" registrado correctamente.', 'success')
            return redirect(url_for('organizacion.documentos'))

    return render_template('organizacion/nuevo_documento.html', categorias=categorias)
