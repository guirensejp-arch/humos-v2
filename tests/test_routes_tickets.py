"""Rutas de tickets imprimibles (80mm): pedido, inventario y caja."""

from datetime import date, timedelta

from app.models.caja import TurnoCaja
from app.models.pedido import Pedido


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


def test_pedido_ticket(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    _crear_pedido(client, datos, cantidad='2')
    pedido = Pedido.query.first()

    respuesta = client.get(f'/pedidos/{pedido.id}/ticket')

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert f'Pedido #{pedido.numero}' in cuerpo
    assert '$ 19.000' in cuerpo


def test_lote_ticket_tras_carga(client, login, datos):
    login('admin@test.com')
    vencimiento = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')

    respuesta = client.post('/inventario/lote/nuevo', data={
        'insumo_id': datos.insumo.id, 'numero': '7', 'cantidad': '3,5',
        'unidad': 'kg', 'fecha_ingreso': '', 'fecha_vencimiento': vencimiento,
    }, follow_redirects=True)

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert 'Carga de insumo' in cuerpo
    assert 'Carne de res' in cuerpo


def test_conteo_ticket_tras_ajuste(client, login, datos):
    login('admin@test.com')

    respuesta = client.post('/inventario/conteo', data={
        f'cantidad_{datos.insumo.id}': '4,0', 'motivo': 'merma',
    }, follow_redirects=True)

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert 'Merma' in cuerpo
    assert 'Carne de res' in cuerpo


def test_compra_ticket(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    vencimiento = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')

    respuesta = client.post('/caja/compras', data={
        'proveedor_id': datos.proveedor.id, 'motivo': 'compra',
        'insumo_id': [datos.insumo.id], 'cantidad': ['2,0'], 'unidad': ['kg'],
        'costo': ['7000'], 'numero': ['55'], 'vencimiento': [vencimiento],
    }, follow_redirects=True)

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert 'Compra a proveedor' in cuerpo
    assert 'Proveedor Test' in cuerpo


def test_tickets_de_caja(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    client.post('/caja/arqueo', data={'efectivo_contado': '1000'}, follow_redirects=True)
    turno = TurnoCaja.query.first()

    cierre = client.get(f'/caja/cierre-z/{turno.id}/ticket')
    assert cierre.status_code == 200
    assert 'Cierre Z' in cierre.get_data(as_text=True)

    arqueo = client.get(f'/caja/arqueo/{turno.id}/ticket')
    assert arqueo.status_code == 200
    assert 'Arqueo' in arqueo.get_data(as_text=True)

    historial = client.get('/caja/historial/ticket?periodo=TODO')
    assert historial.status_code == 200
    assert 'Historial de caja' in historial.get_data(as_text=True)
