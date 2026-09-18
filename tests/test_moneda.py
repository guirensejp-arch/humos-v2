import pytest

from app.utils.moneda import centavos_a_editable, formatear_centavos, parsear_centavos


@pytest.mark.parametrize('texto, esperado', [
    ('$ 8.900', 890000),
    ('8900', 890000),
    ('8900,50', 890050),
    ('8.900,50', 890050),
    ('0,15', 15),
    ('1.500', 150000),
    (8900, 890000),
])
def test_parsear_centavos(texto, esperado):
    assert parsear_centavos(texto) == esperado


@pytest.mark.parametrize('texto', [None, '', '   ', 'abc', '$'])
def test_parsear_centavos_invalido(texto):
    with pytest.raises(ValueError):
        parsear_centavos(texto)


def test_formatear_centavos():
    assert formatear_centavos(890000) == '$ 8.900'
    assert formatear_centavos(3560) == '$ 35,60'
    assert formatear_centavos(890050) == '$ 8.900,50'
    assert formatear_centavos(None) == '$ 0'


def test_centavos_a_editable():
    assert centavos_a_editable(890000) == '8900'
    assert centavos_a_editable(890050) == '8900,50'
    assert centavos_a_editable(None) == ''
