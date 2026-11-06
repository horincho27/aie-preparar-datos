import pytest
from preparar.explorar import informe
from tests.ayudas import hasta

def test_informe_completo_y_conteos():
    tabla = hasta(1)
    resultado = informe(tabla)
    assert set(resultado) == {"filas", "nulos", "duplicados_exactos", "tipos", "tasa_devolucion"}
    assert resultado["filas"] == 2040
    assert resultado["duplicados_exactos"] == 40
    assert resultado["nulos"] == tabla.isna().sum().to_dict()
    assert resultado["nulos"]["price"] == 60
    assert resultado["tipos"] == tabla.dtypes.astype(str).to_dict()
    assert resultado["tasa_devolucion"] == pytest.approx(tabla["returned"].mean())

def test_explorar_no_modifica_la_tabla():
    tabla = hasta(1)
    copia = tabla.copy(deep=True)
    informe(tabla)
    assert tabla.equals(copia)
