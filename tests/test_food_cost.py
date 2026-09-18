from decimal import Decimal
from types import SimpleNamespace

from app.services.food_cost import costo_linea, costo_producto, margen_producto


def _insumo(costo, unidad='kg'):
    return SimpleNamespace(costo=costo, unidad=unidad)


def _linea(insumo, cantidad, unidad):
    return SimpleNamespace(insumo=insumo, cantidad=Decimal(cantidad), unidad=unidad)


def _producto(precio, lineas):
    return SimpleNamespace(precio_venta=precio, insumos=lineas)


def test_costo_linea_misma_unidad():
    carne = _insumo(700000)
    assert costo_linea(_linea(carne, '0.200', 'kg')) == 140000


def test_costo_linea_conversion():
    carne = _insumo(700000, 'kg')
    # 200 g cargados en la receta = 0,2 kg
    assert costo_linea(_linea(carne, '200', 'g')) == 140000


def test_costo_producto_suma_lineas():
    carne = _insumo(700000)
    pan = _insumo(120000)
    producto = _producto(950000, [
        _linea(carne, '0.200', 'kg'),
        _linea(pan, '0.150', 'kg'),
    ])
    assert costo_producto(producto) == 158000


def test_margen_producto():
    carne = _insumo(700000)
    producto = _producto(950000, [_linea(carne, '0.200', 'kg')])
    assert margen_producto(producto) == round((950000 - 140000) * 100 / 950000)


def test_margen_sin_precio():
    assert margen_producto(_producto(0, [])) is None
