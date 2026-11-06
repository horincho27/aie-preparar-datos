import json
from pathlib import Path
from unittest.mock import patch
import joblib
import pandas as pd
from preparar.extraer import cargar_fuentes
from preparar.pipeline import separar, construir_pipeline, ajustar_y_transformar
from preparar.cargar import guardar, aplicar_a_nuevos, preparar_crudos
from tests.ayudas import hasta

RAIZ = Path(__file__).resolve().parents[1]

def test_guardar_tablas_pipeline_y_esquema(tmp_path):
    crudo_train, crudo_test = separar(hasta(7))
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
    train_crudo, test_crudo = separar(hasta(7))
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

def test_produccion_reutiliza_la_misma_preparacion_cruda():
    pedidos, clientes = cargar_fuentes()
    preparada, registro = preparar_crudos(pedidos, clientes)
    pd.testing.assert_frame_equal(preparada, hasta(7))
    assert registro["duplicadas"] == 40 and registro["rechazadas"] == 30
