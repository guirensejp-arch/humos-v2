from datetime import datetime, timedelta

from app.extensions import db
from app.models.caja import CategoriaMovimientoCaja, MovimientoCaja, TipoMovimientoCaja
from app.models.pedido import EstadoPedido, Pedido, PedidoDetalle
from app.services import analitica_service


def _pedido(usuario, total=250000, fecha=None, **kwargs):
    pedido = Pedido(
        numero=kwargs.pop('numero', 1001),
        usuario_id=usuario.id,
        estado=kwargs.pop('estado', EstadoPedido.CONFIRMADO),
        subtotal=total,
        total=total,
        fecha_hora=fecha or datetime.utcnow(),
        **kwargs,
    )
    db.session.add(pedido)
    db.session.flush()
    return pedido


def _detalle(pedido, producto, cantidad, precio):
    db.session.add(PedidoDetalle(
        pedido_id=pedido.id, producto_id=producto.id, cantidad=cantidad,
        precio_unitario=precio, subtotal=cantidad * precio,
    ))


def test_resumen_ventas_pedidos_ticket(fabrica):
    usuario = fabrica.usuario()
    producto = fabrica.producto(precio=100000)
    pedido = _pedido(usuario, total=250000)
    _detalle(pedido, producto, 2, 100000)
    db.session.commit()

    resumen = analitica_service.resumen('DIA')

    assert resumen['ventas'] == 250000
    assert resumen['pedidos'] == 1
    assert resumen['ticket_promedio'] == 250000
    assert resumen['unidades'] == 2


def test_costo_y_margen_estimados(fabrica):
    usuario = fabrica.usuario()
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor, costo=700000, unidad='kg')
    producto = fabrica.producto(precio=950000)
    fabrica.receta(producto, insumo, cantidad='0.200', unidad='kg')
    pedido = _pedido(usuario, total=950000)
    _detalle(pedido, producto, 1, 950000)
    db.session.commit()

    resumen = analitica_service.resumen('DIA')

    assert resumen['costo_estimado'] == 140000  # 0,200 kg × $7.000
    assert resumen['margen_estimado'] == 950000 - 140000


def test_excluye_cancelados(fabrica):
    usuario = fabrica.usuario()
    _pedido(usuario, total=999999, estado=EstadoPedido.CANCELADO)
    db.session.commit()

    resumen = analitica_service.resumen('DIA')

    assert resumen['ventas'] == 0
    assert resumen['pedidos'] == 0


def test_periodos_y_rango_custom(fabrica):
    usuario = fabrica.usuario()
    hoy = datetime.utcnow()
    hace_10 = hoy - timedelta(days=10)
    _pedido(usuario, total=1000, fecha=hoy)
    _pedido(usuario, total=2000, fecha=hace_10)
    db.session.commit()

    assert analitica_service.rango('DIA')['inicio'].date() == datetime.utcnow().date()
    assert analitica_service.resumen('DIA')['ventas'] == 1000
    assert analitica_service.resumen('SEMANA')['ventas'] == 1000
    assert analitica_service.resumen('MES')['ventas'] == 3000
    assert analitica_service.resumen('HISTORICO')['ventas'] == 3000

    desde = hace_10.strftime('%Y-%m-%d')
    assert analitica_service.resumen('DIA', desde=desde)['ventas'] == 3000


def test_agrupacion_por_producto(fabrica):
    usuario = fabrica.usuario()
    a = fabrica.producto(nombre='A', precio=100000)
    b = fabrica.producto(nombre='B', precio=50000)
    pedido = _pedido(usuario, total=250000)
    _detalle(pedido, a, 2, 100000)
    _detalle(pedido, b, 1, 50000)
    db.session.commit()

    filas = analitica_service.productos('DIA')

    assert filas[0]['producto'].id == a.id
    assert filas[0]['unidades'] == 2
    assert filas[0]['facturacion'] == 200000
    assert filas[0]['participacion'] == 80

    por_facturacion = analitica_service.productos('DIA', orden='FACTURACION')
    assert por_facturacion[0]['producto'].id == a.id


def test_agrupacion_por_metodo_pago(fabrica):
    usuario = fabrica.usuario()
    efectivo = fabrica.metodo_pago(nombre='Efectivo')
    tarjeta = fabrica.metodo_pago(nombre='Tarjeta', es_efectivo=False)
    _pedido(usuario, total=100000, metodo_pago_id=efectivo.id)
    _pedido(usuario, total=50000, metodo_pago_id=tarjeta.id)
    db.session.commit()

    filas = {fila['etiqueta']: fila for fila in analitica_service.ventas_por_metodo('DIA')}

    assert filas['Efectivo']['monto'] == 100000
    assert filas['Tarjeta']['monto'] == 50000


def test_comparacion_con_periodo_anterior(fabrica):
    usuario = fabrica.usuario()
    hoy = datetime.utcnow()
    ayer = hoy - timedelta(days=1)
    _pedido(usuario, total=200000, fecha=hoy)
    _pedido(usuario, total=100000, fecha=ayer)
    db.session.commit()

    comparacion = analitica_service.comparacion('DIA')

    assert comparacion['ventas']['actual'] == 200000
    assert comparacion['ventas']['anterior'] == 100000
    assert comparacion['ventas']['variacion'] == 100
    assert analitica_service.comparacion('HISTORICO') is None


def test_clientes_nuevos_y_recurrentes(fabrica):
    usuario = fabrica.usuario()
    hace_10 = datetime.utcnow() - timedelta(days=10)
    recurrente = fabrica.cliente(nombre='Recurrente', telefono='11 1111 1111')
    nuevo = fabrica.cliente(nombre='Nuevo', telefono='11 2222 2222')

    _pedido(usuario, total=1000, fecha=hace_10, cliente_id=recurrente.id)
    _pedido(usuario, total=2000, cliente_id=recurrente.id)
    _pedido(usuario, total=3000, cliente_id=nuevo.id)
    db.session.commit()

    datos = analitica_service.clientes('DIA')

    assert datos['compradores'] == 2
    assert datos['nuevos'] == 1
    assert datos['recurrentes'] == 1


def test_serie_diaria_rellena_dias(fabrica):
    usuario = fabrica.usuario()
    _pedido(usuario, total=1000)
    db.session.commit()

    serie = analitica_service.serie_diaria('SEMANA')

    assert len(serie) == 7
    assert serie[-1]['ventas'] == 1000


def test_caja_flujo(fabrica):
    usuario = fabrica.usuario()
    turno = fabrica.turno(usuario)
    fecha = datetime.utcnow()
    db.session.add_all([
        MovimientoCaja(
            turno_caja_id=turno.id, tipo=TipoMovimientoCaja.VENTA,
            monto=100000, usuario_id=usuario.id, fecha_hora=fecha,
        ),
        MovimientoCaja(
            turno_caja_id=turno.id, tipo=TipoMovimientoCaja.INGRESO,
            monto=5000, usuario_id=usuario.id, fecha_hora=fecha, motivo='extra',
        ),
        MovimientoCaja(
            turno_caja_id=turno.id, tipo=TipoMovimientoCaja.EGRESO,
            categoria=CategoriaMovimientoCaja.PROVEEDOR, monto=20000,
            usuario_id=usuario.id, fecha_hora=fecha, motivo='compra',
        ),
    ])
    db.session.commit()

    caja = analitica_service.caja_flujo('DIA')

    assert caja['ventas'] == 100000
    assert caja['ingresos'] == 5000
    assert caja['egresos'] == 20000
    assert caja['resultado'] == 85000
    assert caja['compras'] == 20000


def test_inventario_detecta_stock_bajo(fabrica):
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor, nombre='Sal', costo=1000, unidad='kg')
    fabrica.lote(insumo, cantidad='0.500')
    db.session.commit()

    inventario = analitica_service.inventario('DIA')

    assert any(insumo.id == i.id for i in inventario['stock_bajo'])
    assert inventario['insumos'] >= 1
