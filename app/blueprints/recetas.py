from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from openpyxl import Workbook

from app.decorators import admin_required
from app.extensions import db
from app.forms import ProductoForm, ProductoInsumoForm
from app.models.proveedor import Insumo
from app.models.receta import Producto, ProductoInsumo
from app.services.food_cost import costo_producto, margen_producto
from app.utils.auditoria import registrar
from app.utils.excel import (
    FORMATO_MONEDA,
    ajustar_anchos,
    formatear_columna,
    marcar_encabezado,
    pesos,
    respuesta_xlsx,
)
from app.utils.moneda import centavos_a_editable, parsear_centavos
from app.utils.numeros import parsear_decimal
from app.utils.unidades import convertir

recetas_bp = Blueprint('recetas', __name__, url_prefix='/recetas')


def _insumos_activos():
    return (
        Insumo.query.filter_by(activo=True).order_by(Insumo.nombre).all()
    )


@recetas_bp.route('/')
@login_required
def lista():
    q = (request.args.get('q') or '').strip()
    categoria = (request.args.get('categoria') or '').strip()

    consulta = Producto.query
    if q:
        consulta = consulta.filter(Producto.nombre.ilike(f'%{q}%'))
    if categoria:
        consulta = consulta.filter(Producto.categoria == categoria)

    productos = consulta.order_by(
        Producto.activo.desc(), Producto.categoria, Producto.nombre
    ).all()
    categorias = [
        c[0]
        for c in db.session.query(Producto.categoria)
        .filter(Producto.categoria.isnot(None))
        .distinct()
        .order_by(Producto.categoria)
        .all()
    ]

    filas = [
        {
            'producto': p,
            'costo': costo_producto(p),
            'margen': margen_producto(p),
        }
        for p in productos
    ]
    return render_template(
        'recetas/lista.html',
        filas=filas,
        categorias=categorias,
        q=q,
        categoria=categoria,
    )


@recetas_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo():
    form = ProductoForm()
    if form.validate_on_submit():
        try:
            precio = parsear_centavos(form.precio_venta.data)
        except ValueError:
            flash('El precio no es un monto válido.', 'danger')
            return render_template('recetas/nuevo.html', form=form)

        producto = Producto(
            nombre=form.nombre.data.strip(),
            descripcion=(form.descripcion.data or '').strip() or None,
            categoria=form.categoria.data or None,
            precio_venta=precio,
            margen_objetivo=form.margen_objetivo.data,
            activo=form.activo.data,
        )
        db.session.add(producto)
        db.session.commit()
        registrar('CREAR_PRODUCTO', 'producto', producto.id)
        flash('Producto creado. Ahora cargá los insumos de la receta.', 'success')
        return redirect(url_for('recetas.detalle', producto_id=producto.id))

    return render_template('recetas/nuevo.html', form=form)


@recetas_bp.route('/<int:producto_id>')
@login_required
def detalle(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    form = ProductoForm(obj=producto)
    form.precio_venta.data = centavos_a_editable(producto.precio_venta)

    linea_form = ProductoInsumoForm()
    linea_form.insumo_id.choices = [(i.id, f'{i.nombre} ({i.unidad})') for i in _insumos_activos()]

    return render_template(
        'recetas/detalle.html',
        producto=producto,
        form=form,
        linea_form=linea_form,
        costo=costo_producto(producto),
        margen=margen_producto(producto),
    )


@recetas_bp.route('/<int:producto_id>/guardar', methods=['POST'])
@login_required
@admin_required
def guardar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    form = ProductoForm()

    if form.validate_on_submit():
        try:
            producto.precio_venta = parsear_centavos(form.precio_venta.data)
        except ValueError:
            flash('El precio no es un monto válido.', 'danger')
            return redirect(url_for('recetas.detalle', producto_id=producto.id))

        producto.nombre = form.nombre.data.strip()
        producto.descripcion = (form.descripcion.data or '').strip() or None
        producto.categoria = form.categoria.data or None
        producto.margen_objetivo = form.margen_objetivo.data
        producto.activo = form.activo.data
        db.session.commit()
        registrar('EDITAR_PRODUCTO', 'producto', producto.id)
        flash('Producto actualizado.', 'success')
    else:
        flash('Revisá los datos del producto.', 'danger')

    return redirect(url_for('recetas.detalle', producto_id=producto.id))


@recetas_bp.route('/<int:producto_id>/insumos', methods=['POST'])
@login_required
@admin_required
def agregar_insumo(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    form = ProductoInsumoForm()
    form.insumo_id.choices = [(i.id, i.nombre) for i in _insumos_activos()]

    if not form.validate_on_submit():
        flash('Revisá los datos del insumo.', 'danger')
        return redirect(url_for('recetas.detalle', producto_id=producto.id))

    insumo = db.session.get(Insumo, form.insumo_id.data)
    if insumo is None or not insumo.activo:
        flash('El insumo no existe o está inactivo.', 'danger')
        return redirect(url_for('recetas.detalle', producto_id=producto.id))

    try:
        cantidad = parsear_decimal(form.cantidad.data)
    except ValueError:
        cantidad = None
    if cantidad is None or cantidad <= 0:
        flash('La cantidad debe ser un número mayor a 0.', 'danger')
        return redirect(url_for('recetas.detalle', producto_id=producto.id))

    if convertir(cantidad, form.unidad.data, insumo.unidad) is None:
        flash(
            f'La unidad {form.unidad.data} no es compatible con la unidad del '
            f'insumo ({insumo.unidad}).',
            'danger',
        )
        return redirect(url_for('recetas.detalle', producto_id=producto.id))

    existente = ProductoInsumo.query.filter_by(
        producto_id=producto.id, insumo_id=insumo.id
    ).first()
    if existente:
        existente.cantidad = cantidad
        existente.unidad = form.unidad.data
        flash('El insumo ya estaba en la receta: se actualizó la cantidad.', 'info')
    else:
        db.session.add(
            ProductoInsumo(
                producto_id=producto.id,
                insumo_id=insumo.id,
                cantidad=cantidad,
                unidad=form.unidad.data,
            )
        )
        flash('Insumo agregado a la receta.', 'success')

    db.session.commit()
    registrar('EDITAR_RECETA', 'producto', producto.id, {'insumo_id': insumo.id})
    return redirect(url_for('recetas.detalle', producto_id=producto.id))


@recetas_bp.route('/<int:producto_id>/insumos/<int:linea_id>/quitar', methods=['POST'])
@login_required
@admin_required
def quitar_insumo(producto_id, linea_id):
    linea = db.get_or_404(ProductoInsumo, linea_id)
    if linea.producto_id != producto_id:
        flash('La línea no pertenece a ese producto.', 'danger')
        return redirect(url_for('recetas.detalle', producto_id=producto_id))

    db.session.delete(linea)
    db.session.commit()
    registrar('EDITAR_RECETA', 'producto', producto_id, {'quitar_insumo': linea.insumo_id})
    flash('Insumo quitado de la receta.', 'info')
    return redirect(url_for('recetas.detalle', producto_id=producto_id))


@recetas_bp.route('/<int:producto_id>/desactivar', methods=['POST'])
@login_required
@admin_required
def desactivar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    producto.activo = False
    db.session.commit()
    registrar('DESACTIVAR_PRODUCTO', 'producto', producto.id)
    flash(f'Producto {producto.nombre} desactivado.', 'info')
    return redirect(url_for('recetas.lista'))


@recetas_bp.route('/<int:producto_id>/activar', methods=['POST'])
@login_required
@admin_required
def activar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    producto.activo = True
    db.session.commit()
    registrar('ACTIVAR_PRODUCTO', 'producto', producto.id)
    flash(f'Producto {producto.nombre} activado.', 'success')
    return redirect(url_for('recetas.lista'))


@recetas_bp.route('/exportar.xlsx')
@login_required
def exportar_xlsx():
    productos = Producto.query.order_by(
        Producto.categoria, Producto.nombre
    ).all()

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Recetas'
    hoja.append(
        ['Producto', 'Categoría', 'Precio venta', 'Costo insumos', 'Margen %', 'Estado']
    )
    for producto in productos:
        margen = margen_producto(producto)
        hoja.append([
            producto.nombre,
            producto.categoria or '',
            pesos(producto.precio_venta),
            pesos(costo_producto(producto)),
            margen if margen is not None else '',
            'Activo' if producto.activo else 'Inactivo',
        ])

    marcar_encabezado(hoja)
    formatear_columna(hoja, 3, FORMATO_MONEDA)
    formatear_columna(hoja, 4, FORMATO_MONEDA)
    ajustar_anchos(hoja)
    hoja.freeze_panes = 'A2'

    return respuesta_xlsx(libro, 'recetas.xlsx')
