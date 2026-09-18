"""Fixtures compartidas para los tests (app en memoria + fábrica de datos)."""

from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    """App con SQLite en memoria y CSRF desactivado (un contexto por test)."""
    aplicacion = create_app('testing')
    with aplicacion.app_context():
        db.create_all()
        yield aplicacion
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login(client):
    def _login(email='admin@test.com', password='password123'):
        return client.post(
            '/auth/login',
            data={'email': email, 'password': password},
            follow_redirects=True,
        )

    return _login


@pytest.fixture()
def fabrica(app):
    """Crea entidades de prueba (hace commit y las devuelve)."""
    from app.models.caja import MetodoPago, TurnoCaja
    from app.models.cliente import Cliente
    from app.models.inventario import Lote
    from app.models.proveedor import Insumo, Proveedor
    from app.models.receta import Producto, ProductoInsumo
    from app.models.usuario import RolUsuario, Usuario

    contador = {'n': 0}

    def _siguiente():
        contador['n'] += 1
        return contador['n']

    class Fabrica:
        def usuario(self, rol=RolUsuario.ADMIN, email=None, nombre='Test', password='password123'):
            numero = _siguiente()
            email = email or f'{rol.value.lower()}{numero}@test.com'
            usuario = Usuario(
                nombre=nombre, apellido='Test', email_personal=email,
                rol=rol, activo=True,
            )
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            return usuario

        def cliente(self, nombre='Lucía', telefono='11 1234 5678', direccion=None):
            from app.services.phone_normalizer import normalize_phone

            cliente = Cliente(
                nombre=nombre, telefono=normalize_phone(telefono), direccion=direccion
            )
            db.session.add(cliente)
            db.session.commit()
            return cliente

        def proveedor(self, nombre='Proveedor Test', rubro='Carnes'):
            proveedor = Proveedor(nombre=nombre, rubro=rubro)
            db.session.add(proveedor)
            db.session.commit()
            return proveedor

        def insumo(self, proveedor=None, nombre='Carne de res', costo=700000, unidad='kg', rubro='Carnes'):
            insumo = Insumo(
                proveedor_id=proveedor.id, nombre=nombre, rubro=rubro,
                costo=costo, unidad=unidad,
            )
            db.session.add(insumo)
            db.session.commit()
            return insumo

        def producto(self, nombre='Cheese Burger Doble', precio=950000, categoria='Hamburguesas', descripcion=None):
            producto = Producto(
                nombre=nombre, descripcion=descripcion, categoria=categoria,
                precio_venta=precio,
            )
            db.session.add(producto)
            db.session.commit()
            return producto

        def receta(self, producto, insumo, cantidad='0.200', unidad='kg'):
            from decimal import Decimal

            linea = ProductoInsumo(
                producto_id=producto.id, insumo_id=insumo.id,
                cantidad=Decimal(str(cantidad)), unidad=unidad,
            )
            db.session.add(linea)
            db.session.commit()
            return linea

        def lote(self, insumo, cantidad='5.000', dias_vencimiento=30, numero='1'):
            from decimal import Decimal

            lote = Lote(
                insumo_id=insumo.id,
                numero=numero,
                cantidad=Decimal(str(cantidad)),
                unidad=insumo.unidad,
                fecha_ingreso=datetime.utcnow(),
                fecha_vencimiento=datetime.combine(
                    date.today() + timedelta(days=dias_vencimiento), time.min
                ),
            )
            db.session.add(lote)
            db.session.commit()
            return lote

        def metodo_pago(self, nombre='Efectivo', es_efectivo=True):
            metodo = MetodoPago(nombre=nombre, es_efectivo=es_efectivo)
            db.session.add(metodo)
            db.session.commit()
            return metodo

        def turno(self, usuario, fondo=100000):
            turno = TurnoCaja(usuario_id=usuario.id, fondo_inicial=fondo)
            db.session.add(turno)
            db.session.commit()
            return turno

    return Fabrica()


@pytest.fixture()
def datos(fabrica):
    """Escenario base: admin, cajero, proveedor/insumo/lote, producto con receta, método."""
    from app.models.usuario import RolUsuario

    admin = fabrica.usuario(rol=RolUsuario.ADMIN, email='admin@test.com', nombre='Admin')
    cajero = fabrica.usuario(rol=RolUsuario.CAJERO, email='cajero@test.com', nombre='Cajero')
    proveedor = fabrica.proveedor()
    insumo = fabrica.insumo(proveedor=proveedor)
    lote = fabrica.lote(insumo, cantidad='5.000')
    producto = fabrica.producto()
    fabrica.receta(producto, insumo, cantidad='0.200')
    metodo = fabrica.metodo_pago()

    return SimpleNamespace(
        admin=admin,
        cajero=cajero,
        proveedor=proveedor,
        insumo=insumo,
        lote=lote,
        producto=producto,
        metodo=metodo,
    )
