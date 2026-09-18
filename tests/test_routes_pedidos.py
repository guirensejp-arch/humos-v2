from decimal import Decimal

from app.models.caja import EstadoTurno, MovimientoCaja, TipoMovimientoCaja, TurnoCaja
from app.models.inventario import MovimientoInventario, TipoMovimientoInventario
from app.models.pedido import EstadoPedido, Pedido


def _abrir_turno(client):
    return client.post(
        '/caja/turno', data={'fondo_inicial': '1.000'}, follow_redirects=True
    )


def _crear_pedido(client, datos, cantidad='2'):
    return client.post('/pedidos/nuevo', data={
        'origen': 'MOSTRADOR', 'tipo_entrega': 'RETIRO',
        'metodo_pago_id': datos.metodo.id,
        'producto_id': [datos.producto.id], 'cantidad': [cantidad],
        'promocion_id': '0', 'descuento': '',
        'pago_procesado_externo': '',
    }, follow_redirects=True)


def test_crear_pedido_descuenta_stock_y_cobra(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)

    respuesta = _crear_pedido(client, datos, cantidad='2')

    assert 'confirmado' in respuesta.get_data(as_text=True)
    pedido = Pedido.query.first()
    assert pedido.estado == EstadoPedido.CONFIRMADO
    assert pedido.total == 1900000
    assert datos.insumo.lotes[0].cantidad == Decimal('4.600')

    salida = MovimientoInventario.query.filter_by(
        tipo=TipoMovimientoInventario.SALIDA
    ).first()
    assert salida is not None and salida.pedido_id == pedido.id

    venta = MovimientoCaja.query.filter_by(tipo=TipoMovimientoCaja.VENTA).first()
    assert venta is not None and venta.monto == 1900000


def test_pedido_sin_turno_bloquea(client, login, datos):
    login('admin@test.com')

    respuesta = _crear_pedido(client, datos, cantidad='1')

    assert 'turno de caja' in respuesta.get_data(as_text=True)
    assert Pedido.query.count() == 0


def test_detalle_estado_y_anular(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    _crear_pedido(client, datos, cantidad='1')
    pedido = Pedido.query.first()

    assert client.get(f'/pedidos/{pedido.id}').status_code == 200

    valido = client.post(
        f'/pedidos/{pedido.id}/estado',
        data={'estado': 'EN_PREPARACION'}, follow_redirects=True,
    )
    assert 'En preparación' in valido.get_data(as_text=True)

    invalido = client.post(
        f'/pedidos/{pedido.id}/estado',
        data={'estado': 'ENTREGADO'}, follow_redirects=True,
    )
    assert 'Estado inválido' in invalido.get_data(as_text=True)

    anulado = client.post(f'/pedidos/{pedido.id}/anular', follow_redirects=True)
    assert 'anulado' in anulado.get_data(as_text=True)
    assert Pedido.query.first().estado == EstadoPedido.CANCELADO
