import pandas as pd
import pytest
from preparar.extraer import cargar_fuentes, unir

def test_lectura_local():
    pedidos, clientes = cargar_fuentes()
    assert isinstance(pedidos, pd.DataFrame) and isinstance(clientes, pd.DataFrame)
    assert len(pedidos) == 2040 and len(clientes) == 400
    assert {"phone", "signup_date", "newsletter"}.issubset(clientes.columns)

def test_union_conserva_pedidos_y_registra_filas():
    pedidos, clientes = cargar_fuentes()
    tabla, registro = unir(pedidos, clientes)
    assert len(tabla) == len(pedidos)
    assert registro == {"antes": 2040, "despues": 2040}
    assert {"phone", "signup_date", "newsletter"}.issubset(tabla.columns)
    pd.testing.assert_frame_equal(pedidos, tabla[pedidos.columns], check_dtype=False)

def test_left_join_y_cliente_no_multiplica_pedidos():
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes.iloc[:1])
    assert len(tabla) == len(pedidos) and tabla["signup_date"].isna().any()
    with pytest.raises(pd.errors.MergeError):
        unir(pedidos, pd.concat([clientes, clientes.iloc[:1]]))
