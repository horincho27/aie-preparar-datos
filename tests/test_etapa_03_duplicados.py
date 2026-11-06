from preparar.duplicados import eliminar_duplicados
from tests.ayudas import hasta

def test_solo_cuarenta_copias_exactas():
    tabla = hasta(1)
    limpia, cantidad = eliminar_duplicados(tabla)
    assert cantidad == 40 and len(limpia) == 2000
    assert not limpia.duplicated().any()
    assert len(tabla) == 2040

def test_compras_legitimas_con_distinto_id_se_conservan():
    limpia, _ = eliminar_duplicados(hasta(1))
    for i in range(20):
        par = limpia[limpia["order_id"].isin([f"O{i:05d}", f"O{1980+i:05d}"])]
        assert len(par) == 2
        assert par["order_id"].nunique() == 2
        assert len(par.drop(columns="order_id").drop_duplicates()) == 1
