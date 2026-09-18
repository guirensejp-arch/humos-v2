"""Cálculo de descuentos de promoción.

Semántica de ``valor`` (doc 3.8):
- ``PORCENTAJE``: centésimos de porcentaje (20% → 2000).
- ``MONTO_FIJO``: centavos.
- ``DOS_POR_UNO``: NULL (llevás 2, pagás 1 sobre los productos alcanzados).
"""

from app.models.promocion import (
    AplicacionPromocion,
    Promocion,
    TipoDescuento,
)


def promociones_vigentes():
    return [p for p in Promocion.query.filter_by(activo=True).all() if p.vigente]


def descuento_promocion(promo, lineas):
    """Descuento en centavos que aplica la promo a las líneas.

    ``lineas`` es una lista de ``(producto, cantidad)``. El descuento se calcula
    solo sobre los productos alcanzados y nunca supera su subtotal.
    """
    afectadas = [(producto, cantidad) for producto, cantidad in lineas if promo.alcanza(producto)]
    if not afectadas:
        return 0

    subtotal_afectado = sum(producto.precio_venta * cantidad for producto, cantidad in afectadas)

    if promo.tipo_descuento == TipoDescuento.PORCENTAJE:
        return int(round(subtotal_afectado * (promo.valor or 0) / 10000))

    if promo.tipo_descuento == TipoDescuento.MONTO_FIJO:
        return min(promo.valor or 0, subtotal_afectado)

    if promo.tipo_descuento == TipoDescuento.DOS_POR_UNO:
        descuento = 0
        for producto, cantidad in afectadas:
            descuento += (cantidad // 2) * producto.precio_venta
        return descuento

    return 0


def mejor_automatica(lineas):
    """Devuelve ``(promo, descuento)`` de la mejor promo automática, o ``(None, 0)``."""
    mejor = None
    mejor_descuento = 0
    for promo in promociones_vigentes():
        if promo.aplicacion != AplicacionPromocion.AUTOMATICA:
            continue
        descuento = descuento_promocion(promo, lineas)
        if descuento > mejor_descuento:
            mejor, mejor_descuento = promo, descuento
    return mejor, mejor_descuento
