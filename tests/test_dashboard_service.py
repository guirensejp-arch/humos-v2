from datetime import datetime

from app.extensions import db
from app.models.pedido import EstadoPedido, Pedido, PedidoDetalle
from app.services import dashboard_service


def _pedido(usuario, estado=EstadoPedido.CONFIRMADO, total=250000):
    pedido = Pedido(
        numero=1001,
        usuario_id=usuario.id,
        estado=estado,
        subtotal=total,
        total=total,
        fecha_hora=datetime.utcnow(),
    )
    db.session.add(pedido)
    db.session.flush()
    return pedido


def test_resumen_ventas_y_ranking(fabrica):
    usuario = fabrica.usuario()
    a = fabrica.producto(nombre='A', precio=100000)
    b = fabrica.producto(nombre='B', precio=50000)
    pedido = _pedido(usuario, total=250000)
    db.session.add(PedidoDetalle(
        pedido_id=pedido.id, producto_id=a.id, cantidad=2,
        precio_unitario=100000, subtotal=200000,
    ))
    db.session.add(PedidoDetalle(
        pedido_id=pedido.id, producto_id=b.id, cantidad=1,
        precio_unitario=50000, subtotal=50000,
    ))
    db.session.commit()

    resumen = dashboard_service.resumen('DIA')

    assert resumen['ventas'] == 250000
    assert resumen['pedidos'] == 1
    assert resumen['ticket_promedio'] == 250000
    assert resumen['mas_vendidos'][0]['producto'].id == a.id
    assert resumen['mas_vendidos'][0]['cantidad'] == 2


def test_resumen_excluye_cancelados(fabrica):
    usuario = fabrica.usuario()
    _pedido(usuario, estado=EstadoPedido.CANCELADO, total=999999)

    resumen = dashboard_service.resumen('DIA')

    assert resumen['ventas'] == 0
    assert resumen['pedidos'] == 0
