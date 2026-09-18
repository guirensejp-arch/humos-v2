from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.caja import (
    CategoriaMovimientoCaja,
    EstadoTurno,
    TipoMovimientoCaja,
)
from app.models.inventario import Lote
from app.services import caja_service


def test_abrir_turno_y_uno_solo(fabrica):
    usuario = fabrica.usuario()

    turno = caja_service.abrir_turno(100000, usuario.id)

    assert turno.estado == EstadoTurno.ABIERTO
    assert caja_service.turno_abierto().id == turno.id
    with pytest.raises(ValueError):
        caja_service.abrir_turno(50000, usuario.id)


def test_efectivo_esperado_y_totales(fabrica):
    usuario = fabrica.usuario()
    metodo = fabrica.metodo_pago()
    turno = caja_service.abrir_turno(100000, usuario.id)

    caja_service.registrar_movimiento(
        turno, TipoMovimientoCaja.VENTA, 50000, usuario.id, metodo_pago_id=metodo.id
    )
    caja_service.registrar_movimiento(
        turno, TipoMovimientoCaja.INGRESO, 5000, usuario.id,
        categoria=CategoriaMovimientoCaja.OTRO, motivo='aporte',
    )
    caja_service.registrar_movimiento(
        turno, TipoMovimientoCaja.EGRESO, 3000, usuario.id,
        categoria=CategoriaMovimientoCaja.GASTO, motivo='gasto',
    )

    assert caja_service.efectivo_esperado(turno) == 152000
    totales = caja_service.totales_cierre(turno)
    assert totales['ventas'] == 50000
    assert totales['ingresos'] == 5000
    assert totales['egresos'] == 3000
    assert totales['total_caja'] == 52000


def test_cerrar_turno_sin_diferencia(fabrica):
    usuario = fabrica.usuario()
    turno = caja_service.abrir_turno(100000, usuario.id)

    arqueo = caja_service.cerrar_turno(turno, 100000, usuario.id)

    assert arqueo.diferencia == 0
    assert turno.estado == EstadoTurno.CERRADO
    assert turno.fecha_cierre is not None


def test_cerrar_turno_con_diferencia_exige_motivo(fabrica):
    usuario = fabrica.usuario()
    turno = caja_service.abrir_turno(100000, usuario.id)

    with pytest.raises(ValueError):
        caja_service.cerrar_turno(turno, 90000, usuario.id)

    with pytest.raises(ValueError):
        caja_service.cerrar_turno(turno, 90000, usuario.id, motivo_diferencia='x')

    arqueo = caja_service.cerrar_turno(
        turno, 90000, usuario.id,
        motivo_diferencia='faltante', diferencia_confirmada=True,
    )
    assert arqueo.diferencia == -10000  # contado - esperado
    assert turno.estado == EstadoTurno.CERRADO


def test_registrar_compra_genera_egreso_y_lote(fabrica):
    usuario = fabrica.usuario()
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor, costo=700000, unidad='kg')
    turno = caja_service.abrir_turno(100000, usuario.id)

    movimiento = caja_service.registrar_compra(
        turno, proveedor,
        [{
            'insumo': insumo,
            'cantidad': Decimal('2'),
            'unidad': 'kg',
            'costo_unitario': 700000,
            'numero': '12',
            'fecha_vencimiento': date.today() + timedelta(days=20),
        }],
        usuario.id,
    )

    assert movimiento.tipo == TipoMovimientoCaja.EGRESO
    assert movimiento.monto == 1400000  # 2 kg * $7000
    assert Lote.query.count() == 1
    assert Lote.query.first().cantidad == Decimal('2.000')
