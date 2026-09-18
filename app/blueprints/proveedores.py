from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from openpyxl import Workbook

from app.decorators import admin_required
from app.extensions import db
from app.forms import ProveedorForm
from app.models.proveedor import Insumo, Proveedor
from app.services.phone_normalizer import formatear_telefono, normalize_phone
from app.utils.auditoria import registrar
from app.utils.excel import (
    FORMATO_MONEDA,
    ajustar_anchos,
    formatear_columna,
    marcar_encabezado,
    pesos,
    respuesta_xlsx,
)

proveedores_bp = Blueprint('proveedores', __name__, url_prefix='/proveedores')


@proveedores_bp.route('/')
@login_required
def lista():
    q = (request.args.get('q') or '').strip()
    rubro = (request.args.get('rubro') or '').strip()

    consulta = Proveedor.query
    if q:
        like = f'%{q}%'
        consulta = consulta.filter(
            db.or_(Proveedor.nombre.ilike(like), Proveedor.rubro.ilike(like))
        )
    if rubro:
        consulta = consulta.filter(Proveedor.rubro == rubro)

    proveedores = consulta.order_by(
        Proveedor.activo.desc(), Proveedor.nombre
    ).all()
    rubros = [
        r[0]
        for r in db.session.query(Proveedor.rubro)
        .distinct()
        .order_by(Proveedor.rubro)
        .all()
    ]
    return render_template(
        'proveedores/lista.html',
        proveedores=proveedores,
        rubros=rubros,
        q=q,
        rubro=rubro,
    )


@proveedores_bp.route('/<int:proveedor_id>')
@login_required
def detalle(proveedor_id):
    proveedor = db.get_or_404(Proveedor, proveedor_id)
    return render_template('proveedores/detalle.html', proveedor=proveedor)


@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo():
    form = ProveedorForm()
    if form.validate_on_submit():
        proveedor = Proveedor(
            nombre=form.nombre.data.strip(),
            rubro=form.rubro.data.strip(),
            telefono=normalize_phone(form.telefono.data),
            notas=(form.notas.data or '').strip() or None,
            activo=form.activo.data,
        )
        db.session.add(proveedor)
        db.session.commit()
        registrar('CREAR_PROVEEDOR', 'proveedor', proveedor.id)
        flash(f'Proveedor {proveedor.nombre} creado.', 'success')
        return redirect(url_for('proveedores.detalle', proveedor_id=proveedor.id))

    return render_template('proveedores/form.html', form=form, proveedor=None)


@proveedores_bp.route('/<int:proveedor_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(proveedor_id):
    proveedor = db.get_or_404(Proveedor, proveedor_id)
    form = ProveedorForm(obj=proveedor)

    if form.validate_on_submit():
        proveedor.nombre = form.nombre.data.strip()
        proveedor.rubro = form.rubro.data.strip()
        proveedor.telefono = normalize_phone(form.telefono.data)
        proveedor.notas = (form.notas.data or '').strip() or None
        proveedor.activo = form.activo.data
        db.session.commit()
        registrar('EDITAR_PROVEEDOR', 'proveedor', proveedor.id)
        flash('Proveedor actualizado.', 'success')
        return redirect(url_for('proveedores.detalle', proveedor_id=proveedor.id))

    return render_template('proveedores/form.html', form=form, proveedor=proveedor)


@proveedores_bp.route('/<int:proveedor_id>/desactivar', methods=['POST'])
@login_required
@admin_required
def desactivar(proveedor_id):
    proveedor = db.get_or_404(Proveedor, proveedor_id)
    proveedor.activo = False
    db.session.commit()
    registrar('DESACTIVAR_PROVEEDOR', 'proveedor', proveedor.id)
    flash(f'Proveedor {proveedor.nombre} desactivado.', 'info')
    return redirect(url_for('proveedores.lista'))


@proveedores_bp.route('/<int:proveedor_id>/activar', methods=['POST'])
@login_required
@admin_required
def activar(proveedor_id):
    proveedor = db.get_or_404(Proveedor, proveedor_id)
    proveedor.activo = True
    db.session.commit()
    registrar('ACTIVAR_PROVEEDOR', 'proveedor', proveedor.id)
    flash(f'Proveedor {proveedor.nombre} activado.', 'success')
    return redirect(url_for('proveedores.lista'))


@proveedores_bp.route('/exportar.xlsx')
@login_required
def exportar_xlsx():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Proveedores'
    hoja.append(['Proveedor', 'Rubro', 'Teléfono', 'Insumos', 'Estado', 'Notas'])
    for proveedor in proveedores:
        hoja.append([
            proveedor.nombre,
            proveedor.rubro,
            formatear_telefono(proveedor.telefono),
            len(proveedor.insumos),
            'Activo' if proveedor.activo else 'Inactivo',
            proveedor.notas or '',
        ])
    marcar_encabezado(hoja)
    ajustar_anchos(hoja)
    hoja.freeze_panes = 'A2'

    hoja_insumos = libro.create_sheet('Insumos')
    hoja_insumos.append(
        ['Proveedor', 'Insumo', 'Rubro', 'Último costo', 'Unidad', 'Estado']
    )
    insumos = Insumo.query.order_by(Insumo.nombre).all()
    for insumo in insumos:
        hoja_insumos.append([
            insumo.proveedor.nombre if insumo.proveedor else '',
            insumo.nombre,
            insumo.rubro or '',
            pesos(insumo.costo),
            insumo.unidad,
            'Activo' if insumo.activo else 'Inactivo',
        ])
    marcar_encabezado(hoja_insumos)
    formatear_columna(hoja_insumos, 4, FORMATO_MONEDA)
    ajustar_anchos(hoja_insumos)
    hoja_insumos.freeze_panes = 'A2'

    return respuesta_xlsx(libro, 'proveedores.xlsx')
