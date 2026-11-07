"""Lo entregado resuelto se prueba sin necesitar las respuestas del alumno."""
import json
from pathlib import Path
from unittest.mock import Mock, patch
import joblib
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from preparar.listo.extraer import cargar_fuentes, unir
from preparar.listo.explorar import informe
from preparar.listo.duplicados import eliminar_duplicados
from preparar.listo.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from preparar.listo.validar import validar, aplicar_reglas
from preparar.listo.enriquecer import precio_unitario
from preparar.listo.pipeline import ajustar_y_transformar, version_mal
from preparar.listo.cargar import guardar, aplicar_a_nuevos, preparar_base, preparar_crudos
from preparar.listo.estado import ejecutar_etapa, EtapaPendiente

RAIZ = Path(__file__).resolve().parents[1]


def tabla_con_tipos():
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes)
    tabla, _ = eliminar_duplicados(tabla)
    tabla["price"] = convertir_precio(tabla["price"])
    tabla["order_date"] = convertir_fecha(tabla["order_date"])
    tabla["category"] = estandarizar_categoria(tabla["category"])
    return tabla


def test_lectura_y_union_sin_perder_filas():
    pedidos, clientes = cargar_fuentes()
    tabla, registro = unir(pedidos, clientes)
    assert len(pedidos) == 2040 and len(clientes) == 400
    assert registro == {"antes": 2040, "despues": 2040}
    assert {"phone", "signup_date", "newsletter"}.issubset(tabla.columns)
    pd.testing.assert_frame_equal(pedidos, tabla[pedidos.columns], check_dtype=False)


def test_left_join_y_cliente_duplicado():
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes.iloc[:1])
    assert len(tabla) == len(pedidos) and tabla["signup_date"].isna().any()
    with pytest.raises(pd.errors.MergeError):
        unir(pedidos, pd.concat([clientes, clientes.iloc[:1]]))


def test_informe_exacto_y_sin_modificaciones():
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes)
    copia = tabla.copy(deep=True)
    resultado = informe(tabla)
    assert set(resultado) == {"filas", "nulos", "duplicados_exactos", "tipos", "tasa_devolucion"}
    assert resultado["filas"] == 2040 and resultado["duplicados_exactos"] == 40
    assert resultado["nulos"] == tabla.isna().sum().to_dict()
    assert resultado["nulos"]["price"] == 60
    assert resultado["tipos"] == tabla.dtypes.astype(str).to_dict()
    assert resultado["tasa_devolucion"] == pytest.approx(tabla["returned"].mean())
    assert tabla.equals(copia)


def test_cuarenta_duplicados_y_compras_legitimas():
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes)
    limpia, cantidad = eliminar_duplicados(tabla)
    assert cantidad == 40 and len(limpia) == 2000
    assert not limpia.duplicated().any() and len(tabla) == 2040
    for i in range(20):
        par = limpia[limpia["order_id"].isin([f"O{i:05d}", f"O{1980+i:05d}"])]
        assert len(par) == 2 and par["order_id"].nunique() == 2
        assert len(par.drop(columns="order_id").drop_duplicates()) == 1


def test_formatos_de_precio_y_vacios():
    resultado = convertir_precio(pd.Series(["1299.90", "$1,299.90", "1299,90", None]))
    assert pd.api.types.is_numeric_dtype(resultado)
    assert resultado.iloc[:3].tolist() == pytest.approx([1299.9] * 3)
    assert pd.isna(resultado.iloc[3])
    assert tabla_con_tipos()["price"].isna().sum() == 60


def test_fechas_explicitas_e_ilegibles():
    resultado = convertir_fecha(pd.Series(["2026-03-14", "14/03/2026", "sin fecha", "04/03/2026"]))
    assert resultado.iloc[0] == resultado.iloc[1] == pd.Timestamp("2026-03-14")
    assert resultado.iloc[3] == pd.Timestamp("2026-03-04") and pd.isna(resultado.iloc[2])
    fechas = tabla_con_tipos()["order_date"]
    assert pd.api.types.is_datetime64_any_dtype(fechas) and fechas.isna().sum() == 5


def test_categorias_normalizadas():
    assert set(tabla_con_tipos()["category"]) == {"ropa", "electrónica", "hogar", "libros"}
    assert estandarizar_categoria(pd.Series(["Ropa", "ropa ", "ROPA"])).nunique() == 1


def test_rechazos_sin_borrar_precios_desconocidos_ni_extremos():
    tabla = tabla_con_tipos()
    validas, cantidad = validar(tabla)
    assert cantidad == 30 and len(validas) == 1970 and len(tabla) == 2000
    assert validas["price"].isna().sum() == 60
    assert validas["price"].dropna().gt(0).all() and validas["price"].eq(99999).sum() == 3
    assert validas["quantity"].gt(0).all() and validas["order_date"].notna().all()


def test_reglas_limitan_veinticinco_descuentos():
    tabla, _ = validar(tabla_con_tipos())
    corregida, cantidad = aplicar_reglas(tabla)
    assert cantidad == 25 and len(corregida) == len(tabla)
    assert corregida["discount"].between(0, 1).all()
    assert corregida.loc[tabla["discount"].gt(1), "discount"].eq(1).all()
    assert corregida.loc[tabla["discount"].lt(0), "discount"].eq(0).all()


def test_precio_unitario_y_division_segura():
    caso = precio_unitario(pd.DataFrame({"price": [100.0, 100.0, None], "quantity": [0, 2, 1]}))
    assert pd.isna(caso.loc[0, "precio_unitario"]) and caso.loc[1, "precio_unitario"] == 50
    assert pd.isna(caso.loc[2, "precio_unitario"])


def test_base_completa_conserva_precio_faltante():
    pedidos, clientes = cargar_fuentes()
    tabla, registro = preparar_base(pedidos, clientes)
    assert registro == {"leidas": 2040, "unidas": 2040, "duplicadas": 40, "rechazadas": 30, "descuentos_limitados": 25, "procesadas": 1970}
    assert tabla["price"].isna().sum() == 60
    assert "phone_missing" not in tabla and "dias_desde_registro" not in tabla


def test_ajustar_guardar_y_aplicar_se_prueban_sin_resolver_etapas(tmp_path):
    # Este transformador mínimo solo sirve para probar la infraestructura:
    # usa una columna y un relleno constante; no resuelve el pipeline de la etapa 3.
    cruda = pd.DataFrame({"order_id": ["A", "B"], "price": [100.0, 400.0], "returned": [0, 1]})
    pipeline = ColumnTransformer([("precio", SimpleImputer(strategy="constant", fill_value=123), ["price"])])
    train, test = ajustar_y_transformar(cruda, cruda.iloc[:1], pipeline)
    guardar(train, test, pipeline, tmp_path)
    assert all((tmp_path / n).exists() for n in ["train.csv", "test.csv", "preparacion.joblib", "esquema.json"])
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / "train.csv", index_col="order_id"), train, check_dtype=False)
    esquema = json.loads((tmp_path / "esquema.json").read_text(encoding="utf-8"))
    assert esquema["columnas_entrada"] == ["price"] and esquema["tipos"] == {"price": "float64"}
    assert esquema["fecha"] and esquema["columnas_salida"] == pipeline.get_feature_names_out().tolist()
    assert joblib.load(tmp_path / "preparacion.joblib").get_feature_names_out().tolist() == pipeline.get_feature_names_out().tolist()
    # Los mocks dejan la tabla intacta: aíslan la infraestructura, no calculan
    # ni el indicador, ni los días, ni la eliminación de columnas del alumno.
    with patch("preparar.listo.cargar.agregar_indicador_faltante", side_effect=lambda tabla, columna: tabla) as indicador, patch("preparar.listo.cargar.dias_desde_registro", side_effect=lambda tabla: tabla) as dias, patch("preparar.listo.cargar.quitar_filtracion", side_effect=lambda tabla: tabla) as quitar, patch.object(type(pipeline), "fit", side_effect=AssertionError("No reajustar")), patch.object(type(pipeline), "fit_transform", side_effect=AssertionError("No reajustar")):
        nuevos = aplicar_a_nuevos(RAIZ / "data/new/orders_new.csv", tmp_path)
    assert len(nuevos) == 196 and nuevos.columns.tolist() == train.columns.drop("returned").tolist()
    assert not nuevos.isna().any().any()
    assert nuevos.attrs["registro"]["rechazadas"] == 4
    indicador.assert_called_once()
    dias.assert_called_once()
    quitar.assert_called_once()


def test_version_mal_ajusta_antes_de_separar():
    tabla = pd.DataFrame({"order_id": ["A", "B", "C"], "price": [10.0, None, 100.0], "returned": [0, 0, 1]})
    minimo = ColumnTransformer([("precio", SimpleImputer(strategy="median"), ["price"])])
    # Aislamos las interfaces pendientes con un transformador de una sola columna
    # y un corte de prueba; no implementamos las dos funciones que debe escribir el alumno.
    with patch("preparar.pipeline.construir_pipeline", return_value=minimo), patch("preparar.pipeline.separar", side_effect=lambda t: (t.iloc[:2], t.iloc[2:])) as corte:
        train, test, aprendido = version_mal(tabla)
    assert aprendido.named_transformers_["precio"].statistics_[0] == 55.0
    assert len(train) + len(test) == len(tabla)
    corte.assert_called_once()


@pytest.mark.parametrize("numero", [1, 2, 3])
def test_mensajes_identifican_la_etapa(numero):
    with pytest.raises(EtapaPendiente, match=f"Falta completar la etapa {numero}"):
        ejecutar_etapa(numero, Mock(side_effect=NotImplementedError))
