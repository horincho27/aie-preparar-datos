from preparar.faltantes import agregar_indicador_faltante, comparar_tasa
from tests.ayudas import hasta

def test_indicador_de_ausencia_y_precio_sin_rellenar():
    tabla = hasta(0)
    resultado = agregar_indicador_faltante(tabla, "phone")
    assert "phone_missing" in resultado
    assert set(resultado["phone_missing"]) == {0, 1}
    assert resultado["phone_missing"].equals(tabla["phone"].isna().astype(int))
    assert resultado["price"].isna().sum() == 60
    assert "phone_missing" not in tabla

def test_la_ausencia_tiene_senal():
    tabla = agregar_indicador_faltante(hasta(0), "phone")
    tasas = comparar_tasa(tabla, "phone_missing")
    assert set(tasas) == {0, 1}
    assert tasas[1] > tasas[0] + 0.20
    assert tasas == tabla.groupby("phone_missing")["returned"].mean().to_dict()
