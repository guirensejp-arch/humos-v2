from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.inventario import MovimientoInventario, TipoMovimientoInventario
from app.services import inventario_service as inv


def _escenario(fabrica):
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor)
    usuario = fabrica.usuario()
    return insumo, usuario


def test_estado_lote(fabrica):
    insumo, _ = _escenario(fabrica)
    assert inv.estado_lote(fabrica.lote(insumo, dias_vencimiento=30)) == inv.ESTADO_OK
    assert inv.estado_lote(fabrica.lote(insumo, dias_vencimiento=1)) == inv.ESTADO_POR_VENCER
    assert inv.estado_lote(fabrica.lote(insumo, dias_vencimiento=-1)) == inv.ESTADO_VENCIDA


def test_stock_insumo_excluye_vencidos_en_disponible(fabrica):
    insumo, _ = _escenario(fabrica)
    fabrica.lote(insumo, cantidad='2.000', dias_vencimiento=10)
    fabrica.lote(insumo, cantidad='3.000', dias_vencimiento=-2)

    assert inv.stock_insumo(insumo) == Decimal('5.000')
    assert inv.stock_disponible(insumo) == Decimal('2.000')


def test_consumir_fefo_usa_el_que_vence_antes(fabrica):
    insumo, usuario = _escenario(fabrica)
    temprano = fabrica.lote(insumo, cantidad='2.000', dias_vencimiento=5, numero='A')
    tarde = fabrica.lote(insumo, cantidad='3.000', dias_vencimiento=20, numero='B')

    inv.consumir_fefo(insumo, Decimal('1.000'), 'test', usuario.id)

    assert temprano.cantidad == Decimal('1.000')
    assert tarde.cantidad == Decimal('3.000')


def test_consumir_fefo_ignora_vencidos(fabrica):
    insumo, usuario = _escenario(fabrica)
    vencido = fabrica.lote(insumo, cantidad='2.000', dias_vencimiento=-3, numero='V')
    vigente = fabrica.lote(insumo, cantidad='3.000', dias_vencimiento=10, numero='O')

    inv.consumir_fefo(insumo, Decimal('1.000'), 'test', usuario.id)

    assert vencido.cantidad == Decimal('2.000')
    assert vigente.cantidad == Decimal('2.000')


def test_consumir_fefo_insuficiente(fabrica):
    insumo, usuario = _escenario(fabrica)
    fabrica.lote(insumo, cantidad='1.000', dias_vencimiento=10)

    with pytest.raises(ValueError):
        inv.consumir_fefo(insumo, Decimal('5.000'), 'test', usuario.id)


def test_aplicar_conteo_merma(fabrica):
    insumo, usuario = _escenario(fabrica)
    fabrica.lote(insumo, cantidad='5.000', dias_vencimiento=10)

    conteo = inv.aplicar_conteo(insumo, Decimal('4.500'), 'merma', usuario.id)

    assert conteo is not None
    assert conteo.diferencia == Decimal('0.500')
    assert inv.stock_disponible(insumo) == Decimal('4.500')
    tipos = {m.tipo for m in MovimientoInventario.query.all()}
    assert TipoMovimientoInventario.MERMA in tipos


def test_aplicar_conteo_sin_diferencia(fabrica):
    insumo, usuario = _escenario(fabrica)
    fabrica.lote(insumo, cantidad='5.000', dias_vencimiento=10)

    assert inv.aplicar_conteo(insumo, Decimal('5.000'), '', usuario.id) is None


def test_aplicar_conteo_sobrante(fabrica):
    insumo, usuario = _escenario(fabrica)
    fabrica.lote(insumo, cantidad='5.000', dias_vencimiento=10)

    conteo = inv.aplicar_conteo(insumo, Decimal('5.500'), 'ajuste', usuario.id)

    assert conteo.diferencia == Decimal('-0.500')
    assert inv.stock_disponible(insumo) == Decimal('5.500')


def test_cargar_lote_valida_unidad(fabrica):
    insumo, usuario = _escenario(fabrica)

    with pytest.raises(ValueError):
        inv.cargar_lote(
            insumo, '1', Decimal('1'), 'ml', None,
            date.today() + timedelta(days=10), usuario.id,
        )


def test_cargar_lote_registra_movimiento_y_convierte(fabrica):
    insumo, usuario = _escenario(fabrica)

    lote = inv.cargar_lote(
        insumo, '9', Decimal('500'), 'g', None,
        date.today() + timedelta(days=10), usuario.id,
    )

    assert lote.cantidad == Decimal('0.500')  # 500 g -> 0.5 kg
    tipos = [m.tipo for m in MovimientoInventario.query.all()]
    assert TipoMovimientoInventario.CARGA in tipos
