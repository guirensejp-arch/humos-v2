from datetime import date, timedelta
from decimal import Decimal

from app.models.inventario import Lote


def test_lista_y_cargar_lote(client, login, datos):
    login('admin@test.com')
    assert client.get('/inventario/').status_code == 200

    vencimiento = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
    respuesta = client.post('/inventario/lote/nuevo', data={
        'insumo_id': datos.insumo.id, 'numero': '7', 'cantidad': '3,5',
        'unidad': 'kg', 'fecha_ingreso': '', 'fecha_vencimiento': vencimiento,
    }, follow_redirects=True)

    assert 'Lote cargado' in respuesta.get_data(as_text=True)
    assert Lote.query.filter_by(numero='7').count() == 1


def test_lote_vencimiento_en_el_pasado_se_rechaza(client, login, datos):
    login('admin@test.com')

    respuesta = client.post('/inventario/lote/nuevo', data={
        'insumo_id': datos.insumo.id, 'numero': '8', 'cantidad': '1',
        'unidad': 'kg', 'fecha_vencimiento': '2020-01-01',
    }, follow_redirects=True)

    assert 'anterior a hoy' in respuesta.get_data(as_text=True)
    assert Lote.query.filter_by(numero='8').count() == 0


def test_conteo_exige_motivo_si_hay_diferencia(client, login, datos):
    login('admin@test.com')

    respuesta = client.post('/inventario/conteo', data={
        f'cantidad_{datos.insumo.id}': '4,0',
    }, follow_redirects=True)

    assert 'obligatorio' in respuesta.get_data(as_text=True)


def test_conteo_aplica_ajuste(client, login, datos):
    login('admin@test.com')

    respuesta = client.post('/inventario/conteo', data={
        f'cantidad_{datos.insumo.id}': '4,0', 'motivo': 'merma',
    }, follow_redirects=True)

    assert 'ajuste' in respuesta.get_data(as_text=True)
    assert datos.insumo.lotes[0].cantidad == Decimal('4.000')
