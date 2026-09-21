from datetime import date, timedelta

from app.models.caja import CategoriaMovimientoCaja, MovimientoCaja, TipoMovimientoCaja
from app.models.cliente import Cliente
from app.models.inventario import Lote
from app.models.proveedor import Insumo, Proveedor
from app.models.receta import Producto, ProductoInsumo


def _abrir_turno(client):
    return client.post(
        '/caja/turno', data={'fondo_inicial': '1.000'}, follow_redirects=True
    )


def test_crear_cliente_normaliza_telefono(client, login, datos):
    login('admin@test.com')

    client.post('/clientes/nuevo', data={
        'nombre': 'Ana', 'apellido': 'Gómez',
        'telefono': '+54 9 11 9876 5432',
        'direccion': '', 'notas': '', 'activo': 'y',
    }, follow_redirects=True)

    cliente = Cliente.query.filter_by(nombre='Ana').first()
    assert cliente is not None
    assert cliente.telefono == '+5491198765432'


def test_cliente_telefono_duplicado(client, login, datos):
    login('admin@test.com')
    client.post('/clientes/nuevo', data={
        'nombre': 'A', 'telefono': '11 1111 1111', 'activo': 'y',
    }, follow_redirects=True)

    respuesta = client.post('/clientes/nuevo', data={
        'nombre': 'B', 'telefono': '+54 9 11 1111 1111', 'activo': 'y',
    }, follow_redirects=True)

    assert 'Ya existe' in respuesta.get_data(as_text=True)


def test_buscar_cliente_por_telefono(client, login, datos):
    login('admin@test.com')
    client.post('/clientes/nuevo', data={
        'nombre': 'Ana', 'telefono': '11 1234 5678', 'activo': 'y',
    }, follow_redirects=True)

    respuesta = client.get('/clientes/buscar?telefono=011 1234 5678')

    datos_json = respuesta.get_json()
    assert datos_json['encontrado'] is True
    assert datos_json['telefono'] == '+5491112345678'


def test_crear_proveedor_e_insumo(client, login, datos):
    login('admin@test.com')

    client.post('/proveedores/nuevo', data={
        'nombre': 'Distribuidora X', 'rubro': 'Carnes',
        'telefono': '', 'notas': '', 'activo': 'y',
    }, follow_redirects=True)
    proveedor = Proveedor.query.filter_by(nombre='Distribuidora X').first()
    assert proveedor is not None

    client.post('/insumos/nuevo', data={
        'proveedor_id': proveedor.id, 'nombre': 'Bondiola', 'rubro': 'Carnes',
        'costo': '5.200', 'unidad': 'kg', 'activo': 'y',
    }, follow_redirects=True)

    insumo = Insumo.query.filter_by(nombre='Bondiola').first()
    assert insumo is not None
    assert insumo.costo == 520000
    assert insumo.proveedor_id == proveedor.id


def test_crear_proveedor_con_descripcion_y_ubicacion(client, login, datos):
    login('admin@test.com')

    client.post('/proveedores/nuevo', data={
        'nombre': 'Granja Sur', 'rubro': 'Verduras',
        'descripcion': 'Verduras de estación', 'ubicacion': 'Ruta 38 km 5',
        'telefono': '', 'notas': '', 'activo': 'y',
    }, follow_redirects=True)

    proveedor = Proveedor.query.filter_by(nombre='Granja Sur').first()
    assert proveedor is not None
    assert proveedor.descripcion == 'Verduras de estación'
    assert proveedor.ubicacion == 'Ruta 38 km 5'


def test_proveedor_detalle_muestra_stock_y_vencimiento(client, login, datos):
    login('admin@test.com')

    respuesta = client.get(f'/proveedores/{datos.proveedor.id}')
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert 'Stock' in html
    assert 'badge-estado-ok' in html


def test_proveedor_lista_muestra_ultima_compra(client, login, datos):
    login('admin@test.com')

    respuesta = client.get('/proveedores/')
    html = respuesta.get_data(as_text=True)

    assert 'Última compra' in html
    assert datos.lote.fecha_ingreso.strftime('%d/%m/%Y') in html


def _compra_insumo_url(datos):
    return f'/proveedores/{datos.proveedor.id}/insumos/{datos.insumo.id}/compra'


def test_compra_insumo_desde_proveedor_genera_egreso_y_lote(client, login, datos):
    login('admin@test.com')
    _abrir_turno(client)
    vencimiento = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')

    respuesta = client.post(_compra_insumo_url(datos), data={
        'cantidad': '2,0', 'unidad': 'kg', 'costo': '8000',
        'numero': '99', 'fecha_vencimiento': vencimiento, 'motivo': 'reposicion',
    }, follow_redirects=True)

    assert 'Compra registrada' in respuesta.get_data(as_text=True)
    assert Lote.query.filter_by(numero='99').count() == 1
    egreso = MovimientoCaja.query.filter_by(tipo=TipoMovimientoCaja.EGRESO).first()
    assert egreso is not None
    assert egreso.categoria == CategoriaMovimientoCaja.PROVEEDOR
    assert egreso.monto == 1600000
    assert datos.insumo.costo == 800000


def test_compra_insumo_sin_turno_no_registra(client, login, datos):
    login('admin@test.com')
    vencimiento = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')
    lotes_antes = Lote.query.count()

    respuesta = client.post(_compra_insumo_url(datos), data={
        'cantidad': '2,0', 'unidad': 'kg', 'costo': '8000',
        'numero': '99', 'fecha_vencimiento': vencimiento, 'motivo': '',
    }, follow_redirects=True)

    assert 'No hay un turno de caja abierto' in respuesta.get_data(as_text=True)
    assert Lote.query.count() == lotes_antes
    assert MovimientoCaja.query.count() == 0


def test_receta_crear_y_agregar_insumo_con_coma(client, login, datos):
    login('admin@test.com')

    client.post('/recetas/nuevo', data={
        'nombre': 'Burger Test', 'descripcion': 'rica',
        'categoria': 'Hamburguesas', 'precio_venta': '9.500',
        'margen_objetivo': '60', 'activo': 'y',
    }, follow_redirects=True)
    producto = Producto.query.filter_by(nombre='Burger Test').first()
    assert producto is not None
    assert producto.precio_venta == 950000

    client.post(f'/recetas/{producto.id}/insumos', data={
        'insumo_id': datos.insumo.id, 'cantidad': '0,200', 'unidad': 'kg',
    }, follow_redirects=True)

    linea = ProductoInsumo.query.filter_by(
        producto_id=producto.id, insumo_id=datos.insumo.id
    ).first()
    assert linea is not None
    assert str(linea.cantidad) == '0.200'
