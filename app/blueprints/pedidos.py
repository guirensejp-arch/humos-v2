from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.forms import CambiarEstadoPedidoForm, PedidoForm
from app.models.caja import MetodoPago
from app.models.cliente import Cliente
from app.models.pedido import (
    CLASES_ESTADO_PEDIDO,
    ETIQUETAS_ESTADO_PEDIDO,
    TRANSICIONES,
    EstadoPedido,
    OrigenPedido,
    Pedido,
    TipoEntrega,
)
from app.models.receta import Producto
from app.models.promocion import Promocion
from app.models.sistema import Auditoria, Configuracion
from app.models.usuario import RolUsuario, Usuario
from app.services import caja_service, pedido_service, promocion_service
from app.services.phone_normalizer import normalize_phone
from app.utils.auditoria import registrar
from app.utils.moneda import parsear_centavos
from app.utils.numeros import parsear_decimal

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')


@pedidos_bp.route('/')
@login_required
@role_required('ADMIN', 'CAJERO')
def lista():
    vista = request.args.get('vista')
    config = Configuracion.get()
    if vista in ('LISTA', 'CUADRICULA'):
        config.vista_pedidos = vista
        db.session.commit()
        return redirect(url_for('pedidos.lista'))

    estado = request.args.get('estado') or ''
    metodo_pago_id = request.args.get('metodo_pago', type=int)
    cadete_id = request.args.get('cadete', type=int)
    desde = request.args.get('desde') or ''
    hasta = request.args.get('hasta') or ''

    consulta = Pedido.query
    if estado:
        try:
            consulta = consulta.filter(Pedido.estado == EstadoPedido(estado))
        except ValueError:
            pass
    if metodo_pago_id:
        consulta = consulta.filter(Pedido.metodo_pago_id == metodo_pago_id)
    if cadete_id:
        consulta = consulta.filter(Pedido.cadete_id == cadete_id)
    if desde:
        consulta = consulta.filter(
            Pedido.fecha_hora >= datetime.strptime(desde, '%Y-%m-%d')
        )
    if hasta:
        consulta = consulta.filter(
            Pedido.fecha_hora
            <= datetime.strptime(hasta, '%Y-%m-%d').replace(hour=23, minute=59)
        )

    pedidos = consulta.order_by(Pedido.fecha_hora.desc()).all()
    metodos = MetodoPago.query.order_by(MetodoPago.nombre).all()
    cadetes = (
        Usuario.query.filter_by(rol=RolUsuario.CADETE, activo=True)
        .order_by(Usuario.nombre)
        .all()
    )

    return render_template(
        'pedidos/lista.html',
        pedidos=pedidos,
        metodos=metodos,
        cadetes=cadetes,
        vista=config.vista_pedidos,
        estado=estado,
        metodo_pago_id=metodo_pago_id,
        cadete_id=cadete_id,
        desde=desde,
        hasta=hasta,
        etiquetas=ETIQUETAS_ESTADO_PEDIDO,
        clases=CLASES_ESTADO_PEDIDO,
    )


def _preparar_form(form):
    form.metodo_pago_id.choices = [(0, '—')] + [
        (m.id, m.nombre) for m in MetodoPago.query.filter_by(activo=True).order_by(MetodoPago.nombre).all()
    ]
    form.cadete_id.choices = [(0, '—')] + [
        (c.id, c.nombre_completo)
        for c in Usuario.query.filter_by(rol=RolUsuario.CADETE, activo=True).order_by(Usuario.nombre).all()
    ]
    form.promocion_id.choices = [(0, 'Automática (mejor)')] + [
        (p.id, p.nombre) for p in promocion_service.promociones_vigentes()
    ]


@pedidos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'CAJERO')
def nuevo():
    form = PedidoForm()
    _preparar_form(form)
    config = Configuracion.get()

    if form.validate_on_submit():
        try:
            lineas = _parsear_lineas_pedido()
            cliente = _resolver_cliente(form)

            metodo_pago = None
            if form.metodo_pago_id.data:
                metodo_pago = db.session.get(MetodoPago, form.metodo_pago_id.data)
            pago_externo = form.pago_procesado_externo.data
            if not pago_externo and metodo_pago is None:
                raise ValueError('Elegí un método de pago.')

            tipo_entrega = TipoEntrega(form.tipo_entrega.data)
            if tipo_entrega == TipoEntrega.MOZO and not config.salon_mozos_activo:
                raise ValueError('El salón/mozos está deshabilitado en Sistema.')

            turno = caja_service.turno_abierto()
            if not pago_externo and turno is None:
                raise ValueError('Abrí un turno de caja antes de cargar pedidos.')

            cadete = (
                db.session.get(Usuario, form.cadete_id.data)
                if form.cadete_id.data else None
            )

            descuento = _resolver_descuento(form.descuento.data, lineas)

            promo = None
            descuento_promo = 0
            if form.promocion_id.data:
                promo = db.session.get(Promocion, form.promocion_id.data)
                if promo is None or not promo.vigente:
                    raise ValueError('La promoción seleccionada no está vigente.')
                descuento_promo = promocion_service.descuento_promocion(promo, lineas)
            else:
                promo, descuento_promo = promocion_service.mejor_automatica(lineas)

            pedido = pedido_service.crear_pedido(
                lineas,
                current_user.id,
                cliente=cliente,
                origen=OrigenPedido(form.origen.data),
                id_externo=form.id_externo.data,
                metodo_pago=metodo_pago,
                pago_procesado_externo=pago_externo,
                tipo_entrega=tipo_entrega,
                cadete=cadete,
                direccion=form.direccion.data or (cliente.direccion if cliente else None),
                notas=form.notas.data,
                descuento=descuento,
                promocion=promo,
                descuento_promocion=descuento_promo,
                turno=turno,
            )
            db.session.commit()
            registrar('CREAR_PEDIDO', 'pedido', pedido.id, {'total': pedido.total})
            flash(f'Pedido #{pedido.numero} confirmado.', 'success')
            return redirect(url_for('pedidos.detalle', pedido_id=pedido.id))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), 'danger')

    productos = (
        Producto.query.filter_by(activo=True)
        .order_by(Producto.categoria, Producto.nombre)
        .all()
    )
    return render_template(
        'pedidos/nuevo.html',
        form=form,
        productos=productos,
        promociones=promocion_service.promociones_vigentes(),
        config=config,
        turno=caja_service.turno_abierto(),
    )


def _parsear_lineas_pedido():
    producto_ids = request.form.getlist('producto_id')
    cantidades = request.form.getlist('cantidad')
    lineas = []
    for posicion, producto_id in enumerate(producto_ids):
        if not producto_id:
            continue
        producto = db.session.get(Producto, int(producto_id))
        if producto is None or not producto.activo:
            raise ValueError('Hay un producto inválido o inactivo.')
        cantidad = int(cantidades[posicion] or 0)
        if cantidad <= 0:
            raise ValueError(f'Cantidad inválida para {producto.nombre}.')
        lineas.append((producto, cantidad))
    if not lineas:
        raise ValueError('Agregá al menos un producto al pedido.')
    return lineas


def _resolver_cliente(form):
    """Usa el cliente elegido o busca/crea uno por teléfono normalizado."""
    if form.cliente_id.data:
        cliente = db.session.get(Cliente, int(form.cliente_id.data))
        if cliente is not None:
            return cliente

    if not form.telefono.data:
        return None  # cliente anónimo/ocasional

    telefono = normalize_phone(form.telefono.data)
    if not telefono:
        raise ValueError('El teléfono no es válido.')

    cliente = Cliente.query.filter_by(telefono=telefono).first()
    if cliente is not None:
        return cliente

    if not (form.nombre.data or '').strip():
        raise ValueError('Para un cliente nuevo hace falta al menos el nombre.')

    cliente = Cliente(
        nombre=form.nombre.data.strip(),
        apellido=(form.apellido.data or '').strip() or None,
        telefono=telefono,
        direccion=(form.direccion.data or '').strip() or None,
        notas=(form.notas.data or '').strip() or None,
    )
    db.session.add(cliente)
    db.session.flush()
    registrar('CREAR_CLIENTE', 'cliente', cliente.id, {'desde': 'pedido'})
    return cliente


def _resolver_descuento(valor, lineas):
    if not valor or not valor.strip():
        return 0
    subtotal = sum(producto.precio_venta * cantidad for producto, cantidad in lineas)
    texto = valor.strip()
    if texto.endswith('%'):
        porcentaje = parsear_decimal(texto[:-1])
        if porcentaje is None or porcentaje < 0 or porcentaje > 100:
            raise ValueError('Porcentaje de descuento inválido.')
        return int(round(subtotal * porcentaje / 100))
    descuento = parsear_centavos(texto)
    if descuento < 0 or descuento > subtotal:
        raise ValueError('El descuento no puede superar el subtotal.')
    return descuento


@pedidos_bp.route('/<int:pedido_id>')
@login_required
@role_required('ADMIN', 'CAJERO')
def detalle(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)
    form = CambiarEstadoPedidoForm()
    form.estado.choices = [
        (estado.value, ETIQUETAS_ESTADO_PEDIDO[estado.value])
        for estado in TRANSICIONES.get(pedido.estado, [])
        if estado != EstadoPedido.CANCELADO
    ]
    historial = (
        Auditoria.query.filter_by(entidad='pedido', entidad_id=pedido.id)
        .order_by(Auditoria.fecha_hora.desc())
        .all()
    )
    return render_template(
        'pedidos/detalle.html',
        pedido=pedido,
        form=form,
        historial=historial,
        etiquetas=ETIQUETAS_ESTADO_PEDIDO,
        clases=CLASES_ESTADO_PEDIDO,
    )


@pedidos_bp.route('/<int:pedido_id>/ticket')
@login_required
@role_required('ADMIN', 'CAJERO')
def ticket(pedido_id):
    """Comprobante de pedido en formato ticket térmico 80mm (imprimible)."""
    pedido = db.get_or_404(Pedido, pedido_id)
    return render_template('tickets/pedido.html', pedido=pedido)


@pedidos_bp.route('/<int:pedido_id>/estado', methods=['POST'])
@login_required
@role_required('ADMIN', 'CAJERO')
def cambiar_estado(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)
    form = CambiarEstadoPedidoForm()
    form.estado.choices = [
        (estado.value, ETIQUETAS_ESTADO_PEDIDO[estado.value])
        for estado in TRANSICIONES.get(pedido.estado, [])
        if estado != EstadoPedido.CANCELADO
    ]
    if form.validate_on_submit():
        try:
            nuevo = EstadoPedido(form.estado.data)
            pedido_service.cambiar_estado(pedido, nuevo)
            db.session.commit()
            registrar(
                'CAMBIAR_ESTADO_PEDIDO', 'pedido', pedido.id,
                {'estado': nuevo.value},
            )
            flash(f'Pedido #{pedido.numero}: {ETIQUETAS_ESTADO_PEDIDO[nuevo.value]}.', 'success')
        except ValueError as error:
            db.session.rollback()
            flash(str(error), 'danger')
    else:
        flash('Estado inválido para este pedido.', 'warning')
    return redirect(url_for('pedidos.detalle', pedido_id=pedido.id))


@pedidos_bp.route('/<int:pedido_id>/anular', methods=['POST'])
@login_required
@role_required('ADMIN', 'CAJERO')
def anular(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)
    try:
        pedido_service.anular_pedido(pedido)
        db.session.commit()
        registrar('ANULAR_PEDIDO', 'pedido', pedido.id)
        flash(f'Pedido #{pedido.numero} anulado.', 'info')
    except ValueError as error:
        db.session.rollback()
        flash(str(error), 'danger')
    return redirect(url_for('pedidos.detalle', pedido_id=pedido.id))
