"""Base de datos ficticia de un mes para Comanda / Humos.

Genera ~1 mes de actividad realista (jueves a domingo, 25-35 pedidos/dia) con:
- Catalogo real: proveedores, insumos, recetas (food cost) y la carta de Humos.
- Turnos de caja: apertura, ventas, compras, gastos/retiros, arqueo y Cierre Z.
- Pedidos: retiro, mostrador, delivery (WhatsApp/PedidosYa/Rappi) y salon (mozo),
  algunos con promocion aplicada.
- Inventario: compras que cargan lotes, FEFO en ventas, conteos con merma y
  lotes por vencer/vencidos para disparar notificaciones.

Uso:
    python seed_mes.py

Reinicia los datos transaccionales (deja usuarios, configuracion y metodos de
pago). Es deterministico (random.seed fijo) salvo la fecha final.
"""

import random
from datetime import date, datetime, time, timedelta
from decimal import ROUND_CEILING, Decimal

from app import create_app
from app.extensions import db
from app.models.caja import (
    Arqueo,
    CategoriaMovimientoCaja,
    EstadoTurno,
    MetodoPago,
    MovimientoCaja,
    TipoMovimientoCaja,
    TurnoCaja,
)
from app.models.cliente import Cliente
from app.models.inventario import (
    Conteo,
    Lote,
    MovimientoInventario,
)
from app.models.notificacion import Notificacion
from app.models.pedido import (
    EstadoPedido,
    OrigenPedido,
    Pedido,
    PedidoDetalle,
    TipoEntrega,
)
from app.models.promocion import (
    AplicacionPromocion,
    Promocion,
    PromocionProducto,
    TipoDescuento,
)
from app.models.proveedor import Insumo, Proveedor
from app.models.receta import Producto, ProductoInsumo
from app.models.sistema import Auditoria, Configuracion
from app.models.usuario import RolUsuario, Usuario
from app.services import caja_service, pedido_service
from app.services.inventario_service import aplicar_conteo, cargar_lote, stock_disponible
from app.services.phone_normalizer import normalize_phone
from app.services.promocion_service import descuento_promocion

random.seed(20260922)

DIAS = 30
FONDO_CAJA = 12_000_000  # $120.000
BUFFER_STOCK = Decimal('2')  # colchón de stock por insumo (kg)
HORARIO = (19, 23)  # ventana de atencion (hora)
# Dias abiertos (weekday): jueves(3), viernes(4), sabado(5), domingo(6)
DIAS_ABIERTOS = (3, 4, 5, 6)


# =============================================================================
# Catalogo
# =============================================================================

PROVEEDORES = {
    'carnes': ('Distribuidora La Estancia', 'Carnes', '11 5555 6666'),
    'lacteos': ('Lácteos del Sur', 'Lácteos', '11 3333 2222'),
    'verduleria': ('Verdulería Don Pedro', 'Vegetales', '11 6666 7777'),
    'panaderia': ('Panadería El Progreso', 'Panificados', '11 4444 5555'),
    'secos': ('Distribuidora del Norte', 'Secos y salsas', '11 2222 9999'),
}

# (nombre, proveedor, rubro, costo centavos/unidad, unidad, shelf life dias)
INSUMOS = [
    ('Carne de res (blend)', 'carnes', 'Carnes', 900_000, 'kg', 75),
    ('Panceta', 'carnes', 'Carnes', 1_400_000, 'kg', 75),
    ('Bondiola de cerdo', 'carnes', 'Carnes', 1_000_000, 'kg', 75),
    ('Costillas de cerdo', 'carnes', 'Carnes', 1_100_000, 'kg', 75),
    ('Tapa de asado', 'carnes', 'Carnes', 1_400_000, 'kg', 75),
    ('Cerdo desmechado', 'carnes', 'Carnes', 950_000, 'kg', 75),
    ('Cheddar', 'lacteos', 'Lácteos', 1_200_000, 'kg', 90),
    ('Provolone', 'lacteos', 'Lácteos', 1_600_000, 'kg', 90),
    ('Manteca ahumada', 'lacteos', 'Lácteos', 800_000, 'kg', 90),
    ('Mayonesa', 'lacteos', 'Lácteos', 400_000, 'kg', 90),
    ('Ketchup', 'lacteos', 'Lácteos', 350_000, 'kg', 90),
    ('Mostaza', 'lacteos', 'Lácteos', 350_000, 'kg', 90),
    ('Aderezo mil islas', 'lacteos', 'Lácteos', 500_000, 'kg', 90),
    ('Mayonesa de apio', 'lacteos', 'Lácteos', 450_000, 'kg', 90),
    ('Mostaza con miel', 'lacteos', 'Lácteos', 600_000, 'kg', 90),
    ('Lechuga', 'verduleria', 'Vegetales', 250_000, 'kg', 40),
    ('Tomate', 'verduleria', 'Vegetales', 280_000, 'kg', 40),
    ('Cebolla', 'verduleria', 'Vegetales', 160_000, 'kg', 45),
    ('Cebolla encurtida', 'verduleria', 'Vegetales', 250_000, 'kg', 45),
    ('Rúcula', 'verduleria', 'Vegetales', 500_000, 'kg', 40),
    ('Repollo', 'verduleria', 'Vegetales', 200_000, 'kg', 45),
    ('Zanahoria', 'verduleria', 'Vegetales', 180_000, 'kg', 45),
    ('Pan de papa', 'panaderia', 'Panificados', 300_000, 'kg', 45),
    ('Salsa BBQ', 'secos', 'Secos y salsas', 400_000, 'kg', 90),
]

# Producto: (nombre, categoria, descripcion, precio centavos, peso, receta)
# receta: lista de (insumo, gramos)
PRODUCTOS = [
    ('Cheese Burger Doble', 'Hamburguesas',
     'Doble carne, doble cheddar, cebolla, ketchup y mostaza', 950_000, 14,
     [('Carne de res (blend)', 220), ('Pan de papa', 150), ('Cheddar', 40),
      ('Cebolla', 20), ('Ketchup', 15), ('Mostaza', 10)]),
    ('Humeante', 'Hamburguesas',
     'Doble carne, doble cheddar, panceta, cebolla, manteca ahumada y aderezo mil islas',
     1_050_000, 12,
     [('Carne de res (blend)', 220), ('Pan de papa', 150), ('Cheddar', 40),
      ('Panceta', 30), ('Cebolla', 20), ('Manteca ahumada', 10),
      ('Aderezo mil islas', 20)]),
    ('Clásica', 'Hamburguesas',
     'Doble carne, doble cheddar, lechuga, tomate y mayonesa', 890_000, 9,
     [('Carne de res (blend)', 220), ('Pan de papa', 150), ('Cheddar', 40),
      ('Lechuga', 20), ('Tomate', 30), ('Mayonesa', 20)]),
    ('Ribs de Cerdo', 'Al plato',
     'Costillas de cerdo ahumadas con salsa BBQ', 1_250_000, 5,
     [('Costillas de cerdo', 400), ('Salsa BBQ', 60)]),
    ('Tapa de Asado', 'Al plato',
     'Corte de res ahumado con aderezo a elección', 1_350_000, 4,
     [('Tapa de asado', 350), ('Aderezo mil islas', 30)]),
    ('Fresco', 'Sándwiches',
     'Tapa de asado ahumada, lechuga, tomate, cebolla encurtida y mayonesa de apio',
     950_000, 8,
     [('Tapa de asado', 180), ('Pan de papa', 150), ('Lechuga', 20),
      ('Tomate', 30), ('Cebolla encurtida', 20), ('Mayonesa de apio', 20)]),
    ('Bandiao', 'Sándwiches',
     'Bondiola ahumada, cheddar y panceta', 980_000, 8,
     [('Bondiola de cerdo', 200), ('Pan de papa', 150), ('Cheddar', 30),
      ('Panceta', 30)]),
    ('Fifi', 'Sándwiches',
     'Bondiola ahumada, queso provolone, rúcula y mostaza con miel', 1_000_000, 6,
     [('Bondiola de cerdo', 200), ('Pan de papa', 150), ('Provolone', 40),
      ('Rúcula', 15), ('Mostaza con miel', 20)]),
    ('Desmechada', 'Sándwiches',
     'Cerdo desmechado con BBQ y coleslaw (en pan de hamburguesa)', 990_000, 7,
     [('Cerdo desmechado', 200), ('Pan de papa', 150), ('Salsa BBQ', 40),
      ('Repollo', 35), ('Zanahoria', 15), ('Mayonesa', 10)]),
]

CLIENTES = [
    ('Lucía', 'García', '11 4567 8901', 'Calle 123, 4° B', 'Sin portero automático'),
    ('Jorge', 'Martínez', '11 3333 4444', 'Av. Siempreviva 742', None),
    ('Ana', 'Fernández', '11 2222 3333', 'Mitre 456', 'Tocar timbre 2 veces'),
    ('Diego', 'Sosa', '11 5050 6060', '9 de Julio 2210', None),
    ('Carla', 'Gómez', '11 4141 5151', 'Belgrano 88, 3° A', 'Dejar en portería'),
    ('Martín', 'Ríos', '11 6161 7171', 'San Martín 1500', None),
    ('Sofía', 'Pereyra', '11 7070 8080', 'Rivadavia 330', None),
    ('Nicolás', 'Luna', '11 8181 9191', 'Los Olivos 12', 'Casa reja verde'),
    ('Paula', 'Torres', '11 9090 1010', 'Constitución 675', None),
    ('Ramiro', 'Castro', '11 1212 3434', 'Pellegrini 900', None),
    ('Julieta', 'Molina', '11 5656 7878', 'Moreno 1420', None),
    ('Federico', 'Bravo', '11 3232 5454', 'Sarmiento 210', 'Edificio azul'),
]

PAGOS_PESO = {
    'Efectivo': 40,
    'QR/Transferencia': 30,
    'Débito': 15,
    'Crédito': 10,
    'MercadoPago': 5,
}

# =============================================================================
# Reset + seed de catalogo
# =============================================================================


def reset_transaccional():
    for modelo in (
        MovimientoInventario, Conteo, Lote, PedidoDetalle, Pedido, Arqueo,
        MovimientoCaja, TurnoCaja, Notificacion, Auditoria, PromocionProducto,
        Promocion, ProductoInsumo, Producto, Insumo, Proveedor, Cliente,
    ):
        modelo.query.delete()
    db.session.commit()


def ensure_usuarios():
    admin = Usuario.query.filter_by(email_personal='admin@comanda.com').first()
    if admin is None:
        admin = Usuario(nombre='Admin', apellido='Sistema',
                        email_personal='admin@comanda.com', rol=RolUsuario.ADMIN)
        admin.set_password('password123')
        db.session.add(admin)
    for nombre, apellido, email, rol in [
        ('Juan', 'Pérez', 'cajero@comanda.com', RolUsuario.CAJERO),
        ('Nico', 'Vera', 'cadete@comanda.com', RolUsuario.CADETE),
    ]:
        if Usuario.query.filter_by(email_personal=email).first() is None:
            usuario = Usuario(nombre=nombre, apellido=apellido,
                              email_personal=email, rol=rol)
            usuario.set_password('password123')
            db.session.add(usuario)
    db.session.commit()
    return admin


def ensure_metodos():
    for nombre, es_efectivo in [('Efectivo', True), ('QR/Transferencia', False),
                                ('Débito', False), ('Crédito', False),
                                ('MercadoPago', False)]:
        if MetodoPago.query.filter_by(nombre=nombre).first() is None:
            db.session.add(MetodoPago(nombre=nombre, es_efectivo=es_efectivo))
    db.session.commit()


def seed_catalogo():
    prov = {}
    for clave, (nombre, rubro, telefono) in PROVEEDORES.items():
        p = Proveedor(nombre=nombre, rubro=rubro, telefono=normalize_phone(telefono))
        db.session.add(p)
        prov[clave] = p
    db.session.flush()

    insumo = {}
    for nombre, proveedor, rubro, costo, unidad, _shelf in INSUMOS:
        i = Insumo(proveedor_id=prov[proveedor].id, nombre=nombre, rubro=rubro,
                   costo=costo, unidad=unidad)
        db.session.add(i)
        insumo[nombre] = i
    db.session.flush()

    for nombre, categoria, descripcion, precio, _peso, receta in PRODUCTOS:
        producto = Producto(nombre=nombre, descripcion=descripcion,
                            categoria=categoria, precio_venta=precio)
        db.session.add(producto)
        db.session.flush()
        for insumo_nombre, gramos in receta:
            db.session.add(ProductoInsumo(
                producto_id=producto.id, insumo_id=insumo[insumo_nombre].id,
                cantidad=Decimal(gramos), unidad='g',
            ))
    db.session.commit()


def seed_clientes():
    for nombre, apellido, telefono, direccion, notas in CLIENTES:
        db.session.add(Cliente(
            nombre=nombre, apellido=apellido, telefono=normalize_phone(telefono),
            direccion=direccion, notas=notas,
        ))
    db.session.commit()


def seed_promos():
    hoy = date.today()
    desde = datetime.combine(hoy - timedelta(days=40), time.min)
    hasta = datetime.combine(hoy + timedelta(days=20), time.max)

    def producto(nombre):
        return Producto.query.filter_by(nombre=nombre).first()

    def crear(nombre, tipo, valor, aplicacion, nombres):
        promo = Promocion(nombre=nombre, tipo_descuento=tipo, valor=valor,
                          aplicacion=aplicacion, vigencia_desde=desde,
                          vigencia_hasta=hasta, activo=True)
        db.session.add(promo)
        db.session.flush()
        for nom in nombres:
            db.session.add(PromocionProducto(
                promocion_id=promo.id, producto_id=producto(nom).id))
        return promo

    crear('2×1 en Cheese Burger Doble', TipoDescuento.DOS_POR_UNO, None,
          AplicacionPromocion.MANUAL, ['Cheese Burger Doble'])
    crear('Happy hour', TipoDescuento.PORCENTAJE, 2000,
          AplicacionPromocion.AUTOMATICA, ['Fresco', 'Bandiao'])
    crear('Combo ahumado', TipoDescuento.PORCENTAJE, 1500,
          AplicacionPromocion.AUTOMATICA, ['Ribs de Cerdo', 'Tapa de Asado'])
    db.session.commit()


# =============================================================================
# Generacion de un dia
# =============================================================================

def _elegir_productos(productos):
    nombres = [p[0] for p in PRODUCTOS]
    pesos = [p[4] for p in PRODUCTOS]
    elegidos = random.choices(nombres, weights=pesos,
                              k=random.choice([1, 1, 2, 2, 3]))
    mapa = {p.nombre: p for p in productos}
    lineas = []
    for nombre in dict.fromkeys(elegidos):
        lineas.append((mapa[nombre], random.choice([1, 1, 1, 1, 2])))
    return lineas


def _armar_pedido(productos, clientes, cadetes, metodos, clientes_frecuentes):
    lineas = _elegir_productos(productos)
    r = random.random()
    if r < 0.40:  # delivery propio (WhatsApp)
        origen, entrega = OrigenPedido.WHATSAPP, TipoEntrega.DELIVERY
        externo = False
    elif r < 0.62:  # apps de delivery (ya cobradas por la plataforma)
        origen = random.choice([OrigenPedido.PEDIDOSYA, OrigenPedido.RAPPI])
        entrega, externo = TipoEntrega.DELIVERY, True
    elif r < 0.85:  # salon
        origen, entrega, externo = OrigenPedido.MOSTRADOR, TipoEntrega.MOZO, False
    else:  # retiro / mostrador
        origen, entrega, externo = OrigenPedido.MOSTRADOR, TipoEntrega.RETIRO, False

    cliente = None
    direccion = None
    cadete = None
    if entrega == TipoEntrega.DELIVERY:
        cliente = random.choice(clientes_frecuentes if random.random() < 0.5
                                else clientes)
        direccion = cliente.direccion or 'Dirección a confirmar'
        if not externo and cadetes:
            cadete = random.choice(cadetes)
    metodo = None
    if not externo:
        pesos = [PAGOS_PESO.get(m.nombre, 1) for m in metodos]
        metodo = random.choices(metodos, weights=pesos)[0]
    return {
        'lineas': lineas, 'origen': origen, 'entrega': entrega,
        'externo': externo, 'cliente': cliente, 'direccion': direccion,
        'cadete': cadete, 'metodo': metodo,
    }


def _descuento_de_pedido(plan, promos):
    """Aplica promo automatica y, a veces, la manual 2x1."""
    lineas = plan['lineas']
    # Manual 2x1 en Cheese Burger Doble
    promo = None
    descuento = 0
    if random.random() < 0.10:
        promo = promos.get('2×1 en Cheese Burger Doble')
        if promo is not None:
            descuento = descuento_promocion(promo, lineas)
    if descuento == 0:
        for nombre in ('Happy hour', 'Combo ahumado'):
            promo_auto = promos.get(nombre)
            if promo_auto is None:
                continue
            d = descuento_promocion(promo_auto, lineas)
            if d > descuento:
                promo, descuento = promo_auto, d
    if descuento == 0:
        promo = None
    return promo, descuento


def _comprar_faltantes(turno, admin, planificados, momento):
    """Abastece el stock faltante para el dia (agrupado por proveedor)."""
    # Refresca relaciones (insumo.lotes) que quedan cacheadas en la sesion.
    db.session.expire_all()
    requeridos = {}
    for plan in planificados:
        for insumo, cantidad in pedido_service.requerimientos_insumos(plan['lineas']).items():
            requeridos[insumo] = requeridos.get(insumo, Decimal('0')) + cantidad

    faltantes_por_proveedor = {}
    for insumo, requerido in requeridos.items():
        disponible = stock_disponible(insumo)
        # Compra hasta cubrir el dia mas un colchon (evita restos <1 kg).
        faltante = (requerido + BUFFER_STOCK) - disponible
        if faltante <= Decimal('0'):
            continue
        # Redondeo hacia arriba a múltiplos de 0.25 kg, con un mínimo de 0.25.
        bolsa = (faltante / Decimal('0.25')).to_integral_value(
            rounding=ROUND_CEILING) * Decimal('0.25')
        if bolsa < Decimal('0.25'):
            bolsa = Decimal('0.25')
        faltantes_por_proveedor.setdefault(insumo.proveedor, []).append((insumo, bolsa))

    for proveedor, items in faltantes_por_proveedor.items():
        lineas = []
        for insumo, cantidad in items:
            shelf = next(s for n, _p, _r, _c, _u, s in INSUMOS
                         if n == insumo.nombre)
            lineas.append({
                'insumo': insumo, 'cantidad': cantidad, 'unidad': 'kg',
                'costo_unitario': insumo.costo,
                'numero': f'{insumo.id:02d}-{random.randint(100, 999)}',
                'fecha_vencimiento': momento.date() + timedelta(days=shelf),
            })
        movimiento = caja_service.registrar_compra(
            turno, proveedor, lineas, admin.id,
            motivo=f'Reposición {proveedor.nombre}')
        movimiento.fecha_hora = momento
        for mov_inv in MovimientoInventario.query.filter_by(
                movimiento_caja_id=movimiento.id).all():
            mov_inv.fecha_hora = momento
            if mov_inv.lote_id:
                db.session.get(Lote, mov_inv.lote_id).fecha_ingreso = momento
    db.session.expire_all()


def _generar_dia(dia, productos, clientes, frecuentes, cadetes, cajeros, metodos,
                 promos, admin):
    turno = caja_service.abrir_turno(FONDO_CAJA, random.choice(cajeros).id)
    turno.fecha_apertura = datetime.combine(dia, time(18, 45))

    n = random.randint(25, 35)
    planes = [_armar_pedido(productos, clientes, cadetes, metodos, frecuentes)
              for _ in range(n)]

    _comprar_faltantes(turno, admin, planes, datetime.combine(dia, time(16, 30)))

    # Horarios crecientes dentro de la ventana de atencion.
    inicio = datetime.combine(dia, time(HORARIO[0], 0))
    fin = datetime.combine(dia, time(HORARIO[1], 59))
    ventana = int((fin - inicio).total_seconds())
    slots = sorted(random.randint(0, ventana) for _ in range(n))

    externos = 0
    for plan, segundo in zip(planes, slots):
        momento = inicio + timedelta(seconds=segundo)
        promo, descuento = _descuento_de_pedido(plan, promos)
        id_externo = None
        if plan['externo']:
            externos += 1
            prefijo = 'PY' if plan['origen'] == OrigenPedido.PEDIDOSYA else 'RP'
            id_externo = f'{prefijo}-{dia.strftime("%d%m")}-{externos:03d}'
        pedido = pedido_service.crear_pedido(
            plan['lineas'], random.choice(cajeros).id,
            cliente=plan['cliente'], origen=plan['origen'],
            id_externo=id_externo, metodo_pago=plan['metodo'],
            pago_procesado_externo=plan['externo'], tipo_entrega=plan['entrega'],
            cadete=plan['cadete'], direccion=plan['direccion'],
            promocion=promo, descuento_promocion=descuento, turno=turno,
        )
        pedido.fecha_hora = momento
        # El turno se cierra al terminar el dia: todos los pedidos historicos
        # quedan entregados (si no, el contador de pendientes del shell seria
        # irreal). Los activos aparecen solo con un turno realmente abierto.
        pedido.estado = EstadoPedido.ENTREGADO
        for mov_inv in MovimientoInventario.query.filter_by(pedido_id=pedido.id).all():
            mov_inv.fecha_hora = momento
        if not plan['externo']:
            venta = (MovimientoCaja.query.filter_by(turno_caja_id=turno.id,
                                                    tipo=TipoMovimientoCaja.VENTA)
                     .order_by(MovimientoCaja.id.desc()).first())
            if venta:
                venta.fecha_hora = momento
        if random.random() < 0.35:
            pedido.notas = random.choice(
                ['Sin cebolla', 'Bien cocida', 'Extra cheddar', 'Sin sal',
                 'Para llevar', 'Cortar al medio'])

    # Egresos varios (gasto / retiro del dueño)
    if random.random() < 0.5:
        gasto = random.choice([850_00, 1_250_00, 2_400_00, 320_00])
        mov = caja_service.registrar_movimiento(
            turno, TipoMovimientoCaja.EGRESO, gasto, admin.id,
            categoria=CategoriaMovimientoCaja.GASTO,
            motivo=random.choice(['Limpieza', 'Gas', 'Hielo', 'Descartables']))
        mov.fecha_hora = datetime.combine(dia, time(20, 15))
    if dia.weekday() == 6 and random.random() < 0.7:  # domingo: retiro
        mov = caja_service.registrar_movimiento(
            turno, TipoMovimientoCaja.EGRESO, random.choice([40_000_00, 60_000_00]),
            admin.id, categoria=CategoriaMovimientoCaja.RETIRO_DUENO,
            motivo='Retiro del dueño')
        mov.fecha_hora = datetime.combine(dia, time(23, 40))

    # Conteo con merma (domingos)
    if dia.weekday() == 6:
        insumo = random.choice([i for i in Insumo.query.all()
                                if stock_disponible(i) > Decimal('2')])
        contada = (stock_disponible(insumo) * Decimal('0.94')).quantize(Decimal('0.001'))
        conteo = aplicar_conteo(insumo, contada, 'Merma de fin de semana', admin.id)
        if conteo is not None:
            conteo.fecha_hora = datetime.combine(dia, time(18, 20))
            for mov_inv in MovimientoInventario.query.filter_by(
                    conteo_id=conteo.id).all():
                mov_inv.fecha_hora = conteo.fecha_hora

    # Arqueo y cierre
    esperado = caja_service.efectivo_esperado(turno)
    r = random.random()
    if r < 0.7:
        contado, motivo, confirmada = esperado, None, False
    else:
        delta = random.choice([-20_00, -15_00, -8_00, 5_00, 12_00, 30_00])
        contado = esperado + delta
        motivo = 'Diferencia de arqueo (vuelto/cambio)'
        confirmada = True
    arqueo = caja_service.cerrar_turno(turno, contado, random.choice(cajeros).id,
                                       motivo_diferencia=motivo,
                                       diferencia_confirmada=confirmada)
    arqueo.fecha_hora = datetime.combine(dia, time(23, 58))
    turno.fecha_cierre = arqueo.fecha_hora
    db.session.commit()


# =============================================================================
# Cierre: lotes vencidos / por vencer y notificaciones
# =============================================================================

def sembrar_alertas(admin):
    """Deja lotes por vencer y vencidos + un conteo que dispara stock bajo."""
    hoy = date.today()
    cheddar = Insumo.query.filter_by(nombre='Cheddar').first()
    if cheddar is not None:
        lote = cargar_lote(cheddar, 'VENC', Decimal('0.8'), 'kg',
                           hoy - timedelta(days=25), hoy - timedelta(days=2),
                           admin.id, motivo='Remanente vencido')
        lote.fecha_ingreso = datetime.combine(hoy - timedelta(days=25), time(11, 0))
        for mov in MovimientoInventario.query.filter_by(lote_id=lote.id).all():
            mov.fecha_hora = lote.fecha_ingreso

    rucula = Insumo.query.filter_by(nombre='Rúcula').first()
    if rucula is not None:
        lote = cargar_lote(rucula, 'PORV', Decimal('0.9'), 'kg',
                           hoy - timedelta(days=20), hoy + timedelta(days=2),
                           admin.id, motivo='Reposición')
        lote.fecha_ingreso = datetime.combine(hoy - timedelta(days=20), time(10, 0))
        for mov in MovimientoInventario.query.filter_by(lote_id=lote.id).all():
            mov.fecha_hora = lote.fecha_ingreso

    # Recuento que deja un insumo con stock bajo (dispara la notificacion).
    provolone = Insumo.query.filter_by(nombre='Provolone').first()
    if provolone is not None and stock_disponible(provolone) > Decimal('0.5'):
        conteo = aplicar_conteo(provolone, Decimal('0.5'), 'Recuento de fin de mes',
                                admin.id)
        if conteo is not None:
            conteo.fecha_hora = datetime.combine(hoy, time(12, 0))
            for mov in MovimientoInventario.query.filter_by(conteo_id=conteo.id).all():
                mov.fecha_hora = conteo.fecha_hora
    db.session.commit()


# =============================================================================
# Resumen
# =============================================================================

def imprimir_resumen():
    pedidos = Pedido.query.all()
    ventas = sum(p.total for p in pedidos)
    externos = [p for p in pedidos if p.pago_procesado_externo]
    ticket = round(ventas / len(pedidos)) if pedidos else 0
    print('\n=== RESUMEN DEL MES ===')
    print(f'Pedidos: {len(pedidos)}  (de los cuales {len(externos)} por apps, ya cobrados)')
    print(f'Ventas registradas (sin apps): {ventas - sum(p.total for p in externos)} centavos')
    print(f'Ventas totales (todas): {ventas} centavos')
    print(f'Ticket promedio: {ticket} centavos')

    ranking = {}
    for p in pedidos:
        for d in p.detalles:
            ranking[d.producto.nombre] = ranking.get(d.producto.nombre, 0) + d.cantidad
    print('Top productos:')
    for nombre, cant in sorted(ranking.items(), key=lambda x: -x[1])[:5]:
        print(f'  {nombre}: {cant} u.')

    compras = (MovimientoCaja.query.filter_by(
        tipo=TipoMovimientoCaja.EGRESO, categoria=CategoriaMovimientoCaja.PROVEEDOR)
        .with_entities(MovimientoCaja.monto).all())
    print(f'Compras a proveedor: {sum(m[0] for m in compras)} centavos')
    print(f'Turnos cerrados: {TurnoCaja.query.filter_by(estado=EstadoTurno.CERRADO).count()}')
    print(f'Lotes: {Lote.query.count()}  ·  Conteos: {Conteo.query.count()}')
    print('Listo. Entrá con admin@comanda.com / password123')


def main():
    app = create_app('development')
    with app.app_context():
        reset_transaccional()
        admin = ensure_usuarios()
        ensure_metodos()
        seed_catalogo()
        seed_clientes()
        seed_promos()

        Configuracion.get().salon_mozos_activo = True
        db.session.commit()

        metodos = MetodoPago.query.filter_by(activo=True).all()
        cajeros = Usuario.query.filter_by(rol=RolUsuario.CAJERO, activo=True).all()
        cadetes = Usuario.query.filter_by(rol=RolUsuario.CADETE, activo=True).all()
        clientes = Cliente.query.all()
        frecuentes = clientes[:4]
        productos = Producto.query.filter_by(activo=True).all()
        promos = {p.nombre: p for p in Promocion.query.all()}

        hoy = date.today()
        inicio = hoy - timedelta(days=DIAS - 1)
        print(f'Generando actividad {inicio} -> {hoy} (jue-dom)...')
        for offset in range(DIAS):
            dia = inicio + timedelta(days=offset)
            if dia.weekday() not in DIAS_ABIERTOS:
                continue
            _generar_dia(dia, productos, clientes, frecuentes, cadetes, cajeros,
                         metodos, promos, admin)
            print(f'  {dia} ({["lun","mar","mié","jue","vie","sáb","dom"][dia.weekday()]}) ok')

        sembrar_alertas(admin)
        imprimir_resumen()


if __name__ == '__main__':
    main()
