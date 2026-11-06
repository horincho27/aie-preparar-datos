import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from preparar.pipeline import separar, construir_pipeline, ajustar_y_transformar, version_mal
from tests.ayudas import hasta

def test_separacion_reproducible_estratificada_y_sin_pedidos_compartidos():
    tabla = hasta(7)
    train, test = separar(tabla)
    otra_train, otra_test = separar(tabla)
    assert len(train) == 1576 and len(test) == 394
    assert set(train["order_id"]).isdisjoint(test["order_id"])
    assert train.equals(otra_train) and test.equals(otra_test)
    assert abs(train["returned"].mean() - test["returned"].mean()) < 0.01

def test_mediana_solo_del_entrenamiento_y_pipeline_completo():
    tabla = hasta(7)
    train, test = separar(tabla)
    pipeline = construir_pipeline()
    assert isinstance(pipeline, ColumnTransformer)
    salida_train, salida_test = ajustar_y_transformar(train, test, pipeline)
    aprendida = pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_[0]
    assert aprendida == pytest.approx(train["price"].median())
    assert not np.isclose(aprendida, tabla["price"].median())
    assert pipeline.named_transformers_["numericas"].named_steps["scaler"].with_std
    assert pipeline.named_transformers_["categoricas"].handle_unknown == "ignore"
    assert salida_train.columns.tolist() == salida_test.columns.tolist()
    assert not salida_train.isna().any().any() and not salida_test.isna().any().any()
    assert salida_train.index.name == "order_id" and "returned" in salida_train

def test_transformar_no_cambia_lo_aprendido_y_ignora_categoria_nueva():
    train, test = separar(hasta(7))
    pipeline = construir_pipeline()
    ajustar_y_transformar(train, test, pipeline)
    antes = pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_.copy()
    entrada = test.drop(columns="returned").set_index("order_id").copy()
    entrada["price"] = 1e8
    entrada["category"] = "categoría nunca vista"
    salida = pipeline.transform(entrada)
    np.testing.assert_array_equal(antes, pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_)
    assert len(salida) == len(test)

def test_version_mal_aprende_la_mediana_del_conjunto_completo():
    tabla = hasta(7)
    train, test, pipeline = version_mal(tabla)
    aprendida = pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_[0]
    assert aprendida == pytest.approx(tabla["price"].median())
    assert len(train) + len(test) == len(tabla)
