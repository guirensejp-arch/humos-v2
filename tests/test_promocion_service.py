from datetime import datetime, timedelta

from app.extensions import db
from app.models.promocion import (
    AplicacionPromocion,
    Promocion,
    PromocionProducto,
    TipoDescuento,
)
from app.services.promocion_service import (
    descuento_promocion,
    mejor_automatica,
    promociones_vigentes,
)


def _promo(fabrica, tipo, valor, productos=(), aplicacion=AplicacionPromocion.MANUAL):
    promo = Promocion(
        nombre='Promo',
        tipo_descuento=tipo,
        valor=valor,
        aplicacion=aplicacion,
        vigencia_desde=datetime.now() - timedelta(days=1),
        vigencia_hasta=datetime.now() + timedelta(days=10),
    )
    db.session.add(promo)
    db.session.flush()
    for producto in productos:
        db.session.add(PromocionProducto(promocion_id=promo.id, producto_id=producto.id))
    db.session.commit()
    return promo


def test_porcentaje(fabrica):
    producto = fabrica.producto(precio=100000)
    promo = _promo(fabrica, TipoDescuento.PORCENTAJE, 2000, [producto])
    assert descuento_promocion(promo, [(producto, 2)]) == 40000


def test_monto_fijo(fabrica):
    producto = fabrica.producto(precio=100000)
    promo = _promo(fabrica, TipoDescuento.MONTO_FIJO, 30000, [producto])
    assert descuento_promocion(promo, [(producto, 2)]) == 30000


def test_monto_fijo_topeado_al_subtotal(fabrica):
    producto = fabrica.producto(precio=100000)
    promo = _promo(fabrica, TipoDescuento.MONTO_FIJO, 300000, [producto])
    assert descuento_promocion(promo, [(producto, 1)]) == 100000


def test_dos_por_uno(fabrica):
    producto = fabrica.producto(precio=100000)
    promo = _promo(fabrica, TipoDescuento.DOS_POR_UNO, None, [producto])
    assert descuento_promocion(promo, [(producto, 2)]) == 100000
    assert descuento_promocion(promo, [(producto, 3)]) == 100000


def test_promo_no_alcanza_producto(fabrica):
    alcanzado = fabrica.producto(nombre='A', precio=100000)
    otro = fabrica.producto(nombre='B', precio=50000)
    promo = _promo(fabrica, TipoDescuento.PORCENTAJE, 2000, [alcanzado])
    assert descuento_promocion(promo, [(otro, 3)]) == 0


def test_mejor_automatica(fabrica):
    producto = fabrica.producto(precio=100000)
    _promo(fabrica, TipoDescuento.PORCENTAJE, 1000, [producto], AplicacionPromocion.AUTOMATICA)
    mejor = _promo(fabrica, TipoDescuento.PORCENTAJE, 2500, [producto], AplicacionPromocion.AUTOMATICA)
    _promo(fabrica, TipoDescuento.PORCENTAJE, 5000, [producto], AplicacionPromocion.MANUAL)

    promo, descuento = mejor_automatica([(producto, 1)])

    assert promo.id == mejor.id
    assert descuento == 25000


def test_vigentes_excluye_vencidas(fabrica):
    vigente = _promo(fabrica, TipoDescuento.PORCENTAJE, 1000)
    vencida = Promocion(
        nombre='Vieja',
        tipo_descuento=TipoDescuento.PORCENTAJE,
        valor=1000,
        aplicacion=AplicacionPromocion.MANUAL,
        vigencia_desde=datetime.now() - timedelta(days=30),
        vigencia_hasta=datetime.now() - timedelta(days=10),
    )
    db.session.add(vencida)
    db.session.commit()

    ids = [p.id for p in promociones_vigentes()]
    assert vigente.id in ids
    assert vencida.id not in ids
