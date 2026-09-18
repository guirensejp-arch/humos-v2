from app.models.cliente import Cliente
from app.models.proveedor import Insumo, Proveedor
from app.models.receta import Producto, ProductoInsumo


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
