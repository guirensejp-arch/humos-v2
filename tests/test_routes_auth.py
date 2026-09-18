from app.extensions import db


def test_login_ok(client, login, datos):
    respuesta = login('admin@test.com')
    assert respuesta.status_code == 200
    assert 'Pedidos' in respuesta.get_data(as_text=True)


def test_login_credenciales_invalidas(client, datos):
    respuesta = client.post(
        '/auth/login',
        data={'email': 'admin@test.com', 'password': 'mala'},
        follow_redirects=True,
    )
    assert 'Credenciales inválidas' in respuesta.get_data(as_text=True)


def test_login_usuario_inactivo(client, fabrica):
    usuario = fabrica.usuario(email='inactivo@test.com')
    usuario.activo = False
    db.session.commit()

    respuesta = client.post(
        '/auth/login',
        data={'email': 'inactivo@test.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert 'Credenciales inválidas' in respuesta.get_data(as_text=True)


def test_cambio_clave_forzado(client, fabrica):
    usuario = fabrica.usuario(email='reset@test.com')
    usuario.debe_cambiar_clave = True
    db.session.commit()

    respuesta = client.post(
        '/auth/login',
        data={'email': 'reset@test.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert 'Nueva contraseña' in respuesta.get_data(as_text=True)


def test_cajero_no_accede_a_usuarios(client, login, datos):
    login('cajero@test.com')

    respuesta = client.get('/usuarios/', follow_redirects=True)

    assert 'No tenés permiso' in respuesta.get_data(as_text=True)


def test_logout(client, login, datos):
    login('admin@test.com')

    respuesta = client.post('/auth/logout', follow_redirects=True)

    assert 'Sesión cerrada' in respuesta.get_data(as_text=True)
