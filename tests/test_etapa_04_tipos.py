import pandas as pd
import pytest
from preparar.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from tests.ayudas import hasta

def test_precios_de_todos_los_formatos_y_vacios():
    resultado = convertir_precio(pd.Series(["1299.90", "$1,299.90", "1299,90", None]))
    assert pd.api.types.is_numeric_dtype(resultado)
    assert resultado.iloc[:3].tolist() == pytest.approx([1299.9] * 3)
    assert pd.isna(resultado.iloc[3])
    tabla = hasta(3)
    assert convertir_precio(tabla["price"]).isna().sum() == 60

def test_fechas_con_formato_explicito():
    resultado = convertir_fecha(pd.Series(["2026-03-14", "14/03/2026", "sin fecha", "04/03/2026"]))
    assert resultado.iloc[0] == resultado.iloc[1] == pd.Timestamp("2026-03-14")
    assert resultado.iloc[3] == pd.Timestamp("2026-03-04")
    assert pd.isna(resultado.iloc[2])
    fechas = convertir_fecha(hasta(3)["order_date"])
    assert pd.api.types.is_datetime64_any_dtype(fechas) and fechas.isna().sum() == 5

def test_cuatro_categorias_tras_normalizar():
    resultado = estandarizar_categoria(hasta(3)["category"])
    assert set(resultado) == {"ropa", "electrónica", "hogar", "libros"}
    assert estandarizar_categoria(pd.Series(["Ropa", "ropa ", "ROPA"])).nunique() == 1
