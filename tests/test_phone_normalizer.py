import pytest

from app.services.phone_normalizer import formatear_telefono, normalize_phone


@pytest.mark.parametrize('entrada', [
    '11 1234 5678',
    '11-1234-5678',
    '+54 9 11 1234 5678',
    '+54 11 1234 5678',
    '011 1234 5678',
    '011 15 1234 5678',
])
def test_normalize_variantes_a_canonico(entrada):
    assert normalize_phone(entrada) == '+5491112345678'


def test_normalize_vacio():
    assert normalize_phone('') is None
    assert normalize_phone(None) is None
    assert normalize_phone('sin numeros') is None


def test_formatear():
    assert formatear_telefono('+5491112345678') == '+54 9 11 1234-5678'
    assert formatear_telefono('') == ''
