from preparar.validar import validar, aplicar_reglas
from tests.ayudas import hasta

def test_treinta_rechazos_sin_borrar_precios_desconocidos():
    tabla = hasta(4)
    validas, cantidad = validar(tabla)
    assert cantidad == 30 and len(validas) == 1970
    assert validas["price"].isna().sum() == 60
    assert validas["price"].dropna().gt(0).all()
    assert validas["quantity"].gt(0).all() and validas["order_date"].notna().all()
    assert len(tabla) == 2000

def test_veinticinco_descuentos_limitados_sin_rechazo():
    tabla, _ = validar(hasta(4))
    corregida, cantidad = aplicar_reglas(tabla)
    assert cantidad == 25 and len(corregida) == len(tabla)
    assert corregida["discount"].between(0, 1).all()
    assert corregida.loc[tabla["discount"].gt(1), "discount"].eq(1).all()
    assert corregida.loc[tabla["discount"].lt(0), "discount"].eq(0).all()

def test_extremos_positivos_no_son_imposibles():
    tabla, _ = validar(hasta(4))
    assert tabla["price"].eq(99999).sum() == 3
