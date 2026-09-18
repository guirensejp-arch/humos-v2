from decimal import Decimal

import pytest

from app.models.caja import TipoMovimientoCaja
from app.models.inventario import MovimientoInventario, TipoMovimientoInventario
from app.models.pedido import EstadoPedido
from app.services import caja_service, pedido_service


def _escenario(fabrica):
    usuario = fabrica.usuario()
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor, costo=700000)
    fabrica.lote(insumo, cantidad='5.000', dias_vencimiento=30)
    producto = fabrica.producto(precio=950000)
    fabrica.receta(producto, insumo, '0.200')
    metodo = fabrica.metodo_pago()
    turno = caja_service.abrir_turno(100000, usuario.id)
    return usuario, insumo, producto, metodo, turno


def test_crear_pedido_descuenta_stock_y_cobra(fabrica):
    usuario, insumo, producto, metodo, turno = _escenario(fabrica)

    pedido = pedido_service.crear_pedido(
        [(producto, 2)], usuario.id, metodo_pago=metodo, turno=turno
    )

    assert pedido.estado == EstadoPedido.CONFIRMADO
    assert pedido.subtotal == 1900000
    assert pedido.total == 1900000
    assert insumo.lotes[0].cantidad == Decimal('4.600')  # 5 - (2 * 0.200)

    salidas = [
        m for m in MovimientoInventario.query.all()
        if m.tipo == TipoMovimientoInventario.SALIDA
    ]
    assert len(salidas) == 1
    assert salidas[0].cantidad == Decimal('-0.400')
    assert salidas[0].pedido_id == pedido.id

    ventas = [m for m in turno.movimientos if m.tipo == TipoMovimientoCaja.VENTA]
    assert len(ventas) == 1
    assert ventas[0].monto == 1900000


def test_stock_insuficiente_bloquea(fabrica):
    usuario = fabrica.usuario()
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor, costo=700000)
    fabrica.lote(insumo, cantidad='0.100', dias_vencimiento=30)
    producto = fabrica.producto(precio=950000)
    fabrica.receta(producto, insumo, '0.200')
    metodo = fabrica.metodo_pago()
    turno = caja_service.abrir_turno(100000, usuario.id)

    with pytest.raises(ValueError):
        pedido_service.crear_pedido(
            [(producto, 1)], usuario.id, metodo_pago=metodo, turno=turno
        )


def test_pago_externo_no_genera_venta(fabrica):
    usuario, _, producto, _, turno = _escenario(fabrica)

    pedido = pedido_service.crear_pedido(
        [(producto, 1)], usuario.id, pago_procesado_externo=True, turno=turno
    )

    assert pedido.metodo_pago_id is None
    ventas = [m for m in turno.movimientos if m.tipo == TipoMovimientoCaja.VENTA]
    assert ventas == []


def test_descuento_manual_reduce_total(fabrica):
    usuario, _, producto, metodo, turno = _escenario(fabrica)

    pedido = pedido_service.crear_pedido(
        [(producto, 1)], usuario.id, metodo_pago=metodo, turno=turno,
        descuento=100000,
    )

    assert pedido.total == 850000


def test_cambiar_estado_valido_e_invalido_y_anular(fabrica):
    usuario, _, producto, metodo, turno = _escenario(fabrica)
    pedido = pedido_service.crear_pedido(
        [(producto, 1)], usuario.id, metodo_pago=metodo, turno=turno
    )

    pedido_service.cambiar_estado(pedido, EstadoPedido.EN_PREPARACION)
    assert pedido.estado == EstadoPedido.EN_PREPARACION

    with pytest.raises(ValueError):
        pedido_service.cambiar_estado(pedido, EstadoPedido.ENTREGADO)

    pedido_service.anular_pedido(pedido)
    assert pedido.estado == EstadoPedido.CANCELADO

    with pytest.raises(ValueError):
        pedido_service.anular_pedido(pedido)
