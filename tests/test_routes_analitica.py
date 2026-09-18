from datetime import datetime

from app.extensions import db
from app.models.pedido import EstadoPedido, Pedido, PedidoDetalle

CONTENT_TYPE_XLSX = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


def _venta(usuario, producto):
    pedido = Pedido(
        numero=1001, usuario_id=usuario.id, estado=EstadoPedido.CONFIRMADO,
        subtotal=100000, total=100000, fecha_hora=datetime.utcnow(),
    )
    db.session.add(pedido)
    db.session.flush()
    db.session.add(PedidoDetalle(
        pedido_id=pedido.id, producto_id=producto.id, cantidad=1,
        precio_unitario=100000, subtotal=100000,
    ))
    db.session.commit()


def test_admin_accede(client, login, datos):
    login('admin@test.com')
    _venta(datos.admin, datos.producto)

    respuesta = client.get('/analitica/')

    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert 'Analítica' in texto
    assert 'Ventas por día' in texto


def test_cajero_denegado(client, login, datos):
    login('cajero@test.com')

    respuesta = client.get('/analitica/', follow_redirects=True)

    assert 'No tenés permiso' in respuesta.get_data(as_text=True)


def test_anonimo_redirigido(client, datos):
    respuesta = client.get('/analitica/')

    assert respuesta.status_code == 302
    assert '/auth/login' in respuesta.headers['Location']


def test_filtros_de_periodo(client, login, datos):
    login('admin@test.com')

    for periodo in ('DIA', 'SEMANA', 'MES', 'HISTORICO'):
        assert client.get(f'/analitica/?periodo={periodo}').status_code == 200

    assert client.get('/analitica/?desde=2026-01-01&hasta=2026-01-31').status_code == 200
    assert client.get('/analitica/?orden=FACTURACION').status_code == 200


def test_export_excel(client, login, datos):
    login('admin@test.com')
    _venta(datos.admin, datos.producto)

    respuesta = client.get('/analitica/exportar.xlsx')

    assert respuesta.status_code == 200
    assert respuesta.headers['Content-Type'] == CONTENT_TYPE_XLSX


def test_export_denegado_a_cajero(client, login, datos):
    login('cajero@test.com')

    respuesta = client.get('/analitica/exportar.xlsx', follow_redirects=True)

    assert 'No tenés permiso' in respuesta.get_data(as_text=True)
