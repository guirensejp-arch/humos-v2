"""Agregados del Dashboard: KPIs y rankings por período."""

from datetime import date, datetime, time, timedelta

from app.models.pedido import EstadoPedido, Pedido
from app.models.receta import Producto
from app.services.food_cost import margen_producto

PERIODOS = {
    'DIA': 'Día',
    'SEMANA': 'Semana',
    'MES': 'Mes',
    'HISTORICO': 'Histórico',
}

_DIAS = {'DIA': 1, 'SEMANA': 7, 'MES': 30}


def resumen(periodo='DIA'):
    desde = None
    if periodo in _DIAS:
        desde = datetime.combine(date.today() - timedelta(days=_DIAS[periodo] - 1), time.min)

    consulta = Pedido.query.filter(Pedido.estado != EstadoPedido.CANCELADO)
    if desde is not None:
        consulta = consulta.filter(Pedido.fecha_hora >= desde)
    pedidos = consulta.all()

    ventas = sum(pedido.total for pedido in pedidos)
    cantidad = len(pedidos)
    ticket_promedio = round(ventas / cantidad) if cantidad else 0

    productos = Producto.query.filter_by(activo=True).all()
    conteos = {producto.id: 0 for producto in productos}
    for pedido in pedidos:
        for detalle in pedido.detalles:
            if detalle.producto_id in conteos:
                conteos[detalle.producto_id] += detalle.cantidad

    ranking = [
        {'producto': producto, 'cantidad': conteos[producto.id]}
        for producto in productos
    ]

    mayor_margen = None
    for producto in productos:
        margen = margen_producto(producto)
        if margen is not None and (mayor_margen is None or margen > mayor_margen[1]):
            mayor_margen = (producto, margen)

    return {
        'ventas': ventas,
        'pedidos': cantidad,
        'ticket_promedio': ticket_promedio,
        'mas_vendidos': sorted(ranking, key=lambda f: f['cantidad'], reverse=True)[:5],
        'menos_vendidos': sorted(ranking, key=lambda f: f['cantidad'])[:5],
        'mayor_margen': mayor_margen,
    }
