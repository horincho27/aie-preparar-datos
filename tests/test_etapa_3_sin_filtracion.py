import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from preparar.pipeline import separar, construir_pipeline
from preparar.listo.pipeline import ajustar_y_transformar
from tests.ayudas import hasta

def test_separacion_reproducible_estratificada_y_sin_pedidos_compartidos():
    tabla = hasta(2)
    train, test = separar(tabla)
    otra_train, otra_test = separar(tabla)
    assert len(train) == 1576 and len(test) == 394
    assert set(train["order_id"]).isdisjoint(test["order_id"])
    assert train.equals(otra_train) and test.equals(otra_test)
    assert abs(train["returned"].mean() - test["returned"].mean()) < 0.01

def test_mediana_solo_del_entrenamiento_y_pipeline_completo():
    tabla = hasta(2)
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
    train, test = separar(hasta(2))
    pipeline = construir_pipeline()
    ajustar_y_transformar(train, test, pipeline)
    antes = pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_.copy()
    entrada = test.drop(columns="returned").set_index("order_id").copy()
    entrada["price"] = 1e8
    entrada["category"] = "categoría nunca vista"
    salida = pipeline.transform(entrada)
    np.testing.assert_array_equal(antes, pipeline.named_transformers_["numericas"].named_steps["imputer"].statistics_)
    assert len(salida) == len(test)



import json
from pathlib import Path
from unittest.mock import patch
import joblib
import pandas as pd
from preparar.listo.extraer import cargar_fuentes
from preparar.pipeline import separar, construir_pipeline
from preparar.listo.pipeline import ajustar_y_transformar
from preparar.listo.cargar import guardar, aplicar_a_nuevos, preparar_crudos
from tests.ayudas import hasta

RAIZ = Path(__file__).resolve().parents[1]

def test_guardar_tablas_pipeline_y_esquema(tmp_path):
    crudo_train, crudo_test = separar(hasta(2))
    pipeline = construir_pipeline()
    train, test = ajustar_y_transformar(crudo_train, crudo_test, pipeline)
    guardar(train, test, pipeline, tmp_path)
    assert all((tmp_path / nombre).exists() for nombre in ["train.csv", "test.csv", "preparacion.joblib", "esquema.json"])
    leida = pd.read_csv(tmp_path / "train.csv", index_col="order_id")
    pd.testing.assert_frame_equal(leida, train, check_dtype=False, atol=1e-10)
    esquema = json.loads((tmp_path / "esquema.json").read_text(encoding="utf-8"))
    assert esquema["columnas_entrada"] == pipeline.feature_names_in_.tolist()
    assert esquema["tipos"] == crudo_train.drop(columns=["returned", "order_id"]).dtypes.astype(str).to_dict()
    assert esquema["fecha"] and esquema["columnas_salida"] == pipeline.get_feature_names_out().tolist()
    assert joblib.load(tmp_path / "preparacion.joblib").get_feature_names_out().tolist() == pipeline.get_feature_names_out().tolist()

def test_produccion_mismas_columnas_categoria_nueva_y_sin_ajustar(tmp_path):
    train_crudo, test_crudo = separar(hasta(2))
    pipeline = construir_pipeline()
    train, test = ajustar_y_transformar(train_crudo, test_crudo, pipeline)
    guardar(train, test, pipeline, tmp_path)
    with patch.object(type(pipeline), "fit", side_effect=AssertionError("Producción no debe ajustar")), patch.object(type(pipeline), "fit_transform", side_effect=AssertionError("Producción no debe ajustar")):
        nuevos = aplicar_a_nuevos(RAIZ / "data/new/orders_new.csv", tmp_path)
    assert nuevos.columns.tolist() == train.columns.drop("returned").tolist()
    assert len(nuevos) == 196 and not nuevos.isna().any().any()
    assert nuevos.index.is_unique and nuevos.index.name == "order_id"
    assert nuevos.attrs["registro"] == {"leidas": 200, "unidas": 200, "duplicadas": 0, "rechazadas": 4, "descuentos_limitados": 3, "procesadas": 196}
    # Los primeros 8 pedidos tienen la categoría nueva y deben llegar a la salida.
    assert {f"N{i:05d}" for i in range(8)}.issubset(nuevos.index)

