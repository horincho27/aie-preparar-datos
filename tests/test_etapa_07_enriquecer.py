import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from preparar.enriquecer import dias_desde_registro, precio_unitario, quitar_filtracion
from tests.ayudas import hasta

def test_dias_se_calculan_al_momento_del_pedido():
    tabla = dias_desde_registro(hasta(6))
    esperados = (tabla["order_date"] - pd.to_datetime(tabla["signup_date"], format="%Y-%m-%d")).dt.days
    assert tabla["dias_desde_registro"].equals(esperados)
    assert tabla["dias_desde_registro"].ge(0).all()

def test_precio_unitario_y_division_segura():
    tabla = precio_unitario(hasta(6))
    assert tabla["precio_unitario"].equals(tabla["price"] / tabla["quantity"])
    caso = precio_unitario(pd.DataFrame({"price": [100.0, 100.0], "quantity": [0, 2]}))
    assert pd.isna(caso.loc[0, "precio_unitario"]) and caso.loc[1, "precio_unitario"] == 50

def test_quita_solo_datos_del_futuro_y_acepta_que_ya_no_existan():
    tabla = hasta(6)
    resultado = quitar_filtracion(tabla)
    assert {"refund_amount", "return_reason"}.isdisjoint(resultado.columns)
    assert set(resultado.columns) == set(tabla.columns) - {"refund_amount", "return_reason"}
    assert quitar_filtracion(resultado).equals(resultado)

def test_un_arbol_descubre_la_trampa_del_reembolso():
    tabla = hasta(6)
    legitima = quitar_filtracion(tabla)
    indices_train, indices_test = train_test_split(tabla.index, test_size=0.2, stratify=tabla["returned"], random_state=42)
    con_fuga = tabla[["refund_amount"]].fillna(0)
    sin_fuga = legitima[["phone_missing", "discount"]]
    puntajes = []
    for entrada in [con_fuga, sin_fuga]:
        arbol = DecisionTreeClassifier(max_depth=2, random_state=42)
        arbol.fit(entrada.loc[indices_train], tabla.loc[indices_train, "returned"])
        puntajes.append(accuracy_score(tabla.loc[indices_test, "returned"], arbol.predict(entrada.loc[indices_test])))
    assert puntajes[0] > 0.99
    assert puntajes[1] < 0.95
    assert puntajes[0] > puntajes[1] + 0.08
