"""Cálculo de food cost y margen (derivados, nunca persistidos).

El food cost se recalcula en vivo: si cambia el costo de un insumo, las recetas
que lo usan reflejan el nuevo valor sin guardar datos duplicados.
"""

from decimal import Decimal

from app.utils.unidades import convertir


def costo_linea(linea):
    """Costo en centavos de una línea de receta (cantidad × costo unitario)."""
    if linea.insumo is None:
        return 0

    cantidad = convertir(linea.cantidad, linea.unidad, linea.insumo.unidad)
    if cantidad is None:
        # Unidad incompatible: no debería ocurrir (se valida al guardar).
        cantidad = Decimal(str(linea.cantidad))

    return int(round(cantidad * Decimal(linea.insumo.costo)))


def costo_producto(producto):
    """Food cost total del producto, en centavos."""
    return sum(costo_linea(linea) for linea in producto.insumos)


def margen_producto(producto):
    """Margen bruto en porcentaje entero, o ``None`` si el precio es 0."""
    if not producto.precio_venta:
        return None
    costo = costo_producto(producto)
    return round((producto.precio_venta - costo) * 100 / producto.precio_venta)
