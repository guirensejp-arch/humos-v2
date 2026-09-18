from decimal import Decimal

from app.utils.unidades import convertir, son_compatibles


def test_convertir_masa():
    assert convertir(200, 'g', 'kg') == Decimal('0.2')
    assert convertir(2, 'kg', 'g') == Decimal('2000')


def test_convertir_volumen():
    assert convertir('1.5', 'l', 'ml') == Decimal('1500')
    assert convertir(500, 'ml', 'l') == Decimal('0.5')


def test_misma_unidad():
    assert convertir(3, 'ud', 'ud') == Decimal('3')


def test_incompatibles():
    assert convertir(1, 'kg', 'ml') is None
    assert not son_compatibles('kg', 'ml')
    assert not son_compatibles('g', 'l')


def test_compatibles():
    assert son_compatibles('kg', 'g')
    assert son_compatibles('l', 'ml')
    assert son_compatibles('ud', 'ud')
