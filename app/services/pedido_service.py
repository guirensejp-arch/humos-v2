"""Lógica de pedidos: alta transaccional (todo-o-nada) con stock y caja.

Al confirmar un pedido se ejecuta, en una única transacción:
pedido + pedido_detalle + descuento de stock por FEFO + movimiento de caja
(VENTA) + movimientos de inventario. Si algo falla, rollback sin estado a medias.
"""

from decimal import Decimal

from app.extensions import db
from app.models.caja import TipoMovimientoCaja
from app.models.inventario import TipoMovimientoInventario
from app.models.pedido import (
    EstadoPedido,
    OrigenPedido,
    Pedido,
    PedidoDetalle,
    TipoEntrega,
)
from app.services import caja_service
from app.services.inventario_service import consumir_fefo, stock_disponible
from app.utils.unidades import convertir


def siguiente_numero():
    """Número interno correlativo (arranca en 1001)."""
    ultimo = db.session.query(db.func.max(Pedido.numero)).scalar()
    return (ultimo or 1000) + 1


def requerimientos_insumos(lineas):
    """Insumos necesarios para las líneas: ``{insumo: Decimal}``.

    Convierte la cantidad de cada línea de receta a la unidad del insumo y la
    multiplica por la cantidad pedida. Lanza ``ValueError`` si hay unidades
    incompatibles.
    """
    requeridos = {}
    for producto, cantidad in lineas:
        for linea in producto.insumos:
            cantidad_insumo = convertir(linea.cantidad, linea.unidad, linea.insumo.unidad)
            if cantidad_insumo is None:
                raise ValueError(
                    f'Unidad incompatible en la receta de {producto.nombre}.'
                )
            requeridos[linea.insumo] = (
                requeridos.get(linea.insumo, Decimal('0'))
                + cantidad_insumo * cantidad
            )
    return requeridos


def validar_stock(lineas):
    """Verifica que haya stock vigente suficiente. Devuelve los requeridos."""
    requeridos = requerimientos_insumos(lineas)
    for insumo, requerido in requeridos.items():
        disponible = stock_disponible(insumo)
        if disponible < requerido:
            raise ValueError(
                f'Sin stock suficiente de {insumo.nombre}: '
                f'necesario {requerido} {insumo.unidad}, disponible {disponible}.'
            )
    return requeridos


def crear_pedido(
    lineas,
    usuario_id,
    cliente=None,
    origen=OrigenPedido.MOSTRADOR,
    id_externo=None,
    metodo_pago=None,
    pago_procesado_externo=False,
    tipo_entrega=TipoEntrega.RETIRO,
    cadete=None,
    direccion=None,
    notas=None,
    descuento=0,
    promocion=None,
    descuento_promocion=0,
    turno=None,
):
    """Confirma un pedido completo (transacción a cargo del caller con commit)."""
    if not lineas:
        raise ValueError('El pedido no tiene productos.')
    for producto, cantidad in lineas:
        if cantidad is None or cantidad <= 0:
            raise ValueError(f'Cantidad inválida para {producto.nombre}.')

    subtotal = sum(producto.precio_venta * cantidad for producto, cantidad in lineas)
    if descuento < 0 or descuento > subtotal:
        raise ValueError('El descuento no puede superar el subtotal.')
    if descuento_promocion < 0 or descuento_promocion > subtotal - descuento:
        raise ValueError('El descuento de la promoción no puede superar el subtotal.')
    total = subtotal - descuento - descuento_promocion

    if not pago_procesado_externo and metodo_pago is None:
        raise ValueError('El método de pago es obligatorio.')

    requeridos = validar_stock(lineas)

    pedido = Pedido(
        numero=siguiente_numero(),
        origen=origen,
        id_externo=(id_externo or '').strip() or None,
        cliente_id=cliente.id if cliente else None,
        usuario_id=usuario_id,
        metodo_pago_id=metodo_pago.id if metodo_pago else None,
        pago_procesado_externo=pago_procesado_externo,
        tipo_entrega=tipo_entrega,
        cadete_id=cadete.id if cadete else None,
        direccion=(direccion or '').strip() or None,
        notas=(notas or '').strip() or None,
        estado=EstadoPedido.CONFIRMADO,
        descuento=descuento,
        descuento_promocion=descuento_promocion,
        subtotal=subtotal,
        total=total,
        promocion_id=promocion.id if promocion else None,
        turno_caja_id=turno.id if turno else None,
    )
    db.session.add(pedido)
    db.session.flush()

    for producto, cantidad in lineas:
        db.session.add(
            PedidoDetalle(
                pedido_id=pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                subtotal=producto.precio_venta * cantidad,
            )
        )
    db.session.flush()

    # Descuento de stock por FEFO (todo-o-nada con el resto de la transacción).
    for insumo, requerido in requeridos.items():
        consumir_fefo(
            insumo, requerido, f'Pedido #{pedido.numero}', usuario_id,
            tipo=TipoMovimientoInventario.SALIDA, pedido_id=pedido.id,
        )

    # Asiento de venta en caja, salvo que la plataforma ya haya cobrado.
    if not pago_procesado_externo and turno is not None:
        caja_service.registrar_movimiento(
            turno,
            TipoMovimientoCaja.VENTA,
            total,
            usuario_id,
            metodo_pago_id=metodo_pago.id,
            motivo=f'Venta pedido #{pedido.numero}',
        )

    return pedido


def anular_pedido(pedido):
    """Anula un pedido (nunca borra). No revierte stock/caja en v1."""
    if pedido.estado in (EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO):
        raise ValueError('El pedido ya está entregado o anulado.')
    pedido.estado = EstadoPedido.CANCELADO
    db.session.flush()
    return pedido


def cambiar_estado(pedido, nuevo_estado):
    from app.models.pedido import TRANSICIONES

    if nuevo_estado not in TRANSICIONES.get(pedido.estado, []):
        raise ValueError(
            f'No se puede pasar de {pedido.estado.value} a {nuevo_estado.value}.'
        )
    pedido.estado = nuevo_estado
    db.session.flush()
    return pedido
