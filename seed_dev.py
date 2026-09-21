"""Datos de desarrollo (Días 1 y 2).

Uso:
    python seed_dev.py

Crea (si no existen) usuarios, clientes, proveedores, insumos y productos de
ejemplo. Es idempotente: se puede correr varias veces sin duplicar.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models.caja import MetodoPago
from app.models.cliente import Cliente
from app.models.inventario import Lote
from app.models.pedido import EstadoPedido, OrigenPedido, Pedido, TipoEntrega
from app.models.promocion import (
    AplicacionPromocion,
    Promocion,
    PromocionProducto,
    TipoDescuento,
)
from app.models.proveedor import Insumo, Proveedor
from app.models.receta import Producto
from app.models.usuario import RolUsuario, Usuario
from app.services import caja_service, pedido_service
from app.services.inventario_service import cargar_lote
from app.services.phone_normalizer import normalize_phone


def seed_usuarios():
    usuarios = [
        ('Admin', 'Sistema', 'admin@comanda.com', RolUsuario.ADMIN),
        ('Juan', 'Pérez', 'cajero@comanda.com', RolUsuario.CAJERO),
    ]
    for nombre, apellido, email, rol in usuarios:
        if Usuario.query.filter_by(email_personal=email).first():
            continue
        usuario = Usuario(
            nombre=nombre, apellido=apellido, email_personal=email,
            rol=rol, activo=True,
        )
        usuario.set_password('password123')
        db.session.add(usuario)
        print(f'Usuario creado: {email} ({rol.value})')


def _proveedor(nombre, rubro, telefono=None, descripcion=None, ubicacion=None):
    proveedor = Proveedor.query.filter_by(nombre=nombre).first()
    if proveedor is None:
        proveedor = Proveedor(
            nombre=nombre,
            rubro=rubro,
            telefono=normalize_phone(telefono),
            descripcion=descripcion,
            ubicacion=ubicacion,
        )
        db.session.add(proveedor)
        db.session.flush()
        print(f'Proveedor creado: {nombre}')
    return proveedor


def _insumo(proveedor, nombre, rubro, costo, unidad):
    insumo = Insumo.query.filter_by(proveedor_id=proveedor.id, nombre=nombre).first()
    if insumo is None:
        insumo = Insumo(
            proveedor_id=proveedor.id, nombre=nombre, rubro=rubro,
            costo=costo, unidad=unidad,
        )
        db.session.add(insumo)
        db.session.flush()
        print(f'  Insumo: {nombre} ({costo} centavos/{unidad})')
    return insumo


def seed_clientes():
    clientes = [
        ('Lucía', 'García', '11 4567 8901', 'Calle 123, 4° B', 'Sin portero automático'),
        ('Jorge', 'Martínez', '11 3333 4444', None, None),
        ('Ana', 'Fernández', '11 2222 3333', None, None),
    ]
    for nombre, apellido, telefono, direccion, notas in clientes:
        telefono = normalize_phone(telefono)
        if Cliente.query.filter_by(telefono=telefono).first():
            continue
        db.session.add(Cliente(
            nombre=nombre, apellido=apellido, telefono=telefono,
            direccion=direccion, notas=notas,
        ))
        print(f'Cliente creado: {apellido}, {nombre}')


def seed_catalogo():
    carnes = _proveedor(
        'Distribuidora La Estancia', 'Carnes', '11 5555 6666',
        descripcion='Cortes vacunos y de cerdo. Entrega martes y viernes.',
        ubicacion='Av. Roca 1200, Tafí Viejo',
    )
    panificados = _proveedor(
        'Panadería El Progreso', 'Panificados', '11 4444 5555',
        descripcion='Panes artesanales y preelaborados.',
        ubicacion='Belgrano 450, Tafí Viejo',
    )
    lacteos = _proveedor(
        'Lácteos del Sur', 'Lácteos', '11 3333 2222',
        descripcion='Quesos, cremas y salsas.',
        ubicacion='Ruta 9 km 12, Yerba Buena',
    )

    _insumo(carnes, 'Carne de res', 'Carnes', 700000, 'kg')
    _insumo(lacteos, 'Cheddar', 'Lácteos', 700000, 'kg')
    _insumo(lacteos, 'Salsa ahumada', 'Lácteos', 225000, 'kg')
    _insumo(panificados, 'Pan de papa', 'Panificados', 120000, 'kg')


# Carta real de HUMOS (landing guirensejp-arch.github.io/humos-demo).
# La carta original no publica precios: los montos son PLACEHOLDERS de ejemplo
# (en centavos) para que el demo funcione; el negocio debe ajustarlos.
CARTA = [
    ('Hamburguesas', [
        ('Cheese Burger Doble', 'Doble carne, doble cheddar, cebolla, ketchup y mostaza', 950000),
        ('Humeante', 'Doble carne, doble cheddar, panceta, cebolla, manteca ahumada y aderezo mil islas', 1050000),
        ('Clásica', 'Doble carne, doble cheddar, lechuga, tomate y mayonesa', 890000),
    ]),
    ('Al plato', [
        ('Ribs de Cerdo', 'Costillas de cerdo ahumadas con salsa BBQ', 1250000),
        ('Tapa de Asado', 'Corte de res ahumado con aderezo a elección', 1350000),
    ]),
    ('Sándwiches', [
        ('Fresco', 'Tapa de asado ahumada, lechuga, tomate, cebolla encurtida y mayonesa de apio', 950000),
        ('Bandiao', 'Bondiola ahumada, cheddar y panceta', 980000),
        ('Fifi', 'Bondiola ahumada, queso provolone, rúcula y mostaza con miel', 1000000),
        ('Desmechada', 'Cerdo desmechado con BBQ y coleslaw (en pan de hamburguesa)', 990000),
    ]),
]

# Productos del demo anterior que la carta real reemplaza.
LEGACY = ['Burguer Smoked', 'Papas fritas', 'Bebida artesanal']


def seed_carta():
    """Carga la carta de HUMOS (precios placeholder, ajustables)."""
    for categoria, items in CARTA:
        for nombre, descripcion, precio in items:
            if Producto.query.filter_by(nombre=nombre).first():
                continue
            db.session.add(Producto(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                precio_venta=precio,
            ))
            print(f'  Carta: {nombre} ({categoria})')

    for nombre in LEGACY:
        producto = Producto.query.filter_by(nombre=nombre).first()
        if producto and producto.activo:
            producto.activo = False
            print(f'  Producto demo desactivado: {nombre}')


def seed_inventario():
    if Lote.query.first():
        return

    admin = Usuario.query.filter_by(email_personal='admin@comanda.com').first()
    if admin is None:
        return

    hoy = date.today()
    lotes = [
        ('Carne de res', '12', '3.200', 'kg', hoy - timedelta(days=6), hoy + timedelta(days=10)),
        ('Pan de papa', '41', '2.000', 'kg', hoy - timedelta(days=2), hoy + timedelta(days=5)),
        ('Pan de papa', '38', '1.500', 'kg', hoy - timedelta(days=5), hoy + timedelta(days=2)),
        ('Cheddar', '38', '0.800', 'kg', hoy - timedelta(days=7), hoy + timedelta(days=1)),
        ('Cheddar', '32', '0.000', 'kg', hoy - timedelta(days=19), hoy - timedelta(days=2)),
        ('Salsa ahumada', '09', '1.200', 'kg', hoy - timedelta(days=3), hoy + timedelta(days=30)),
    ]

    for nombre, numero, cantidad, unidad, ingreso, vence in lotes:
        insumo = Insumo.query.filter_by(nombre=nombre).first()
        if insumo is None:
            continue
        cargar_lote(
            insumo, numero, Decimal(cantidad), unidad, ingreso, vence, admin.id
        )
        print(f'  Lote {nombre} #{numero} ({cantidad} {unidad})')


def seed_metodos_pago():
    metodos = [
        ('Efectivo', True),
        ('QR/Transferencia', False),
        ('Débito', False),
        ('Crédito', False),
        ('MercadoPago', False),
    ]
    for nombre, es_efectivo in metodos:
        if MetodoPago.query.filter_by(nombre=nombre).first():
            continue
        db.session.add(MetodoPago(nombre=nombre, es_efectivo=es_efectivo))
        print(f'  Método de pago: {nombre}')


def seed_pedidos():
    if Pedido.query.first():
        return

    cajero = Usuario.query.filter_by(email_personal='cajero@comanda.com').first()
    metodo = MetodoPago.query.filter_by(nombre='Efectivo').first()
    cheese = Producto.query.filter_by(nombre='Cheese Burger Doble').first()
    clasica = Producto.query.filter_by(nombre='Clásica').first()
    cliente = Cliente.query.filter(Cliente.nombre == 'Lucía').first()
    if not (cajero and metodo and cheese):
        return

    turno = caja_service.turno_abierto()
    if turno is None:
        turno = caja_service.abrir_turno(500000, cajero.id)  # fondo $5.000

    pedido = pedido_service.crear_pedido(
        [(cheese, 2), (clasica, 1)],
        cajero.id,
        cliente=cliente,
        origen=OrigenPedido.MOSTRADOR,
        metodo_pago=metodo,
        tipo_entrega=TipoEntrega.RETIRO,
        descuento=0,
        turno=turno,
    )
    print(f'  Pedido de ejemplo #{pedido.numero}')
    pedido_service.cambiar_estado(pedido, EstadoPedido.EN_PREPARACION)


def seed_promociones():
    if Promocion.query.first():
        return

    hoy = date.today()
    cheese = Producto.query.filter_by(nombre='Cheese Burger Doble').first()
    fresco = Producto.query.filter_by(nombre='Fresco').first()
    bandiao = Producto.query.filter_by(nombre='Bandiao').first()
    humeante = Producto.query.filter_by(nombre='Humeante').first()

    def _crear(nombre, tipo, valor, aplicacion, desde, hasta, productos):
        promo = Promocion(
            nombre=nombre,
            tipo_descuento=tipo,
            valor=valor,
            aplicacion=aplicacion,
            vigencia_desde=datetime.combine(desde, datetime.min.time()),
            vigencia_hasta=datetime.combine(hasta, datetime.max.time()),
        )
        db.session.add(promo)
        db.session.flush()
        for producto in productos:
            if producto is not None:
                db.session.add(
                    PromocionProducto(promocion_id=promo.id, producto_id=producto.id)
                )
        print(f'  Promoción: {nombre}')

    _crear('2×1 en Cheese Burger Doble', TipoDescuento.DOS_POR_UNO, None,
           AplicacionPromocion.MANUAL, hoy - timedelta(days=1), hoy + timedelta(days=15),
           [cheese])
    _crear('Happy hour', TipoDescuento.PORCENTAJE, 2000,
           AplicacionPromocion.AUTOMATICA, hoy - timedelta(days=1), hoy + timedelta(days=30),
           [fresco, bandiao])
    _crear('Invierno ahumado', TipoDescuento.PORCENTAJE, 3000,
           AplicacionPromocion.MANUAL, hoy - timedelta(days=60), hoy - timedelta(days=10),
           [humeante])


def seed_dev():
    app = create_app('development')
    with app.app_context():
        db.create_all()
        seed_usuarios()
        db.session.flush()
        seed_clientes()
        seed_catalogo()
        seed_carta()
        seed_inventario()
        seed_metodos_pago()
        seed_pedidos()
        seed_promociones()
        db.session.commit()

        print('\nCredenciales de prueba:')
        print('  admin@comanda.com  / password123  (ADMIN)')
        print('  cajero@comanda.com / password123  (CAJERO)')


if __name__ == '__main__':
    seed_dev()
