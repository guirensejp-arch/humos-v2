from datetime import date, timedelta

from app.models.caja import EstadoTurno, MovimientoCaja, TipoMovimientoCaja, TurnoCaja
from app.models.inventario import Lote


def _abrir_turno(client):
    return client.post(
        '/caja/turno', data={'fondo_inicial': '1.000'}, follow_redirects=True
    )


def test_abrir_turno(client, login, datos):
    login('admin@test.com')

    respuesta = _abrir_turno(client)

    assert 'Turno abierto' in respuesta.get_data(as_text=True)
    assert TurnoCaja.query.filter_by(estado=EstadoTurno.ABIERTO).count() == 1


def test_registrar_movimiento(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)

    respuesta = client.post('/caja/movimientos', data={
        'tipo': 'EGRESO', 'monto': '500', 'categoria': 'GASTO',
        'proveedor_id': '0', 'motivo': 'limpieza',
    }, follow_redirects=True)

    assert 'Movimiento registrado' in respuesta.get_data(as_text=True)
    assert MovimientoCaja.query.filter_by(tipo=TipoMovimientoCaja.EGRESO).count() == 1


def test_compra_genera_egreso_y_lote(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    vencimiento = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')

    respuesta = client.post('/caja/compras', data={
        'proveedor_id': datos.proveedor.id, 'motivo': 'compra',
        'insumo_id': [datos.insumo.id], 'cantidad': ['2,0'], 'unidad': ['kg'],
        'costo': ['7000'], 'numero': ['55'], 'vencimiento': [vencimiento],
    }, follow_redirects=True)

    assert 'Compra registrada' in respuesta.get_data(as_text=True)
    assert Lote.query.filter_by(numero='55').count() == 1
    egreso = MovimientoCaja.query.filter_by(tipo=TipoMovimientoCaja.EGRESO).first()
    assert egreso is not None
    assert egreso.monto == 1400000


def test_arqueo_regla_dura_y_cierre(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)

    bloqueado = client.post('/caja/arqueo', data={
        'efectivo_contado': '900', 'motivo_diferencia': '',
        'diferencia_confirmada': '',
    }, follow_redirects=True)
    assert 'confirmarla' in bloqueado.get_data(as_text=True)
    assert TurnoCaja.query.filter_by(estado=EstadoTurno.CERRADO).count() == 0

    cerrado = client.post('/caja/arqueo', data={
        'efectivo_contado': '900', 'motivo_diferencia': 'faltante',
        'diferencia_confirmada': 'y',
    }, follow_redirects=True)
    assert cerrado.status_code == 200
    assert 'Cierre Z' in cerrado.get_data(as_text=True)
    assert TurnoCaja.query.filter_by(estado=EstadoTurno.CERRADO).count() == 1


def test_historial_y_export(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    client.post('/caja/arqueo', data={'efectivo_contado': '1000'}, follow_redirects=True)

    assert client.get('/caja/historial').status_code == 200
    assert client.get('/caja/historial?periodo=TODO').status_code == 200
    assert client.get('/caja/historial/exportar.xlsx?periodo=TODO').status_code == 200
