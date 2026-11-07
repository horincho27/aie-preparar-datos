# Ejecuta el ajuste correcto y conserva los nombres de las columnas.
# Corresponde a la parte de la clase sobre entrenamiento y prueba.
# version_mal reproduce el error de aprender antes de separar para compararlo.
import pandas as pd
from sklearn.compose import ColumnTransformer

def ajustar_y_transformar(train: pd.DataFrame, test: pd.DataFrame, pipeline: ColumnTransformer) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe particiones crudas y pipeline; devuelve tablas numéricas con returned.

    Pista: el ajuste ocurre una vez y solo ve train; usá order_id como índice.
    """
    # Tampoco se entrega la etiqueta al transformador.
    entrada_train = train.drop(columns="returned").set_index("order_id")
    entrada_test = test.drop(columns="returned").set_index("order_id")
    pipeline.fit(entrada_train)
    pipeline.tipos_entrada_ = entrada_train.dtypes.astype(str).to_dict()
    nombres = pipeline.get_feature_names_out()
    salida_train = pd.DataFrame(pipeline.transform(entrada_train), columns=nombres, index=entrada_train.index)
    salida_test = pd.DataFrame(pipeline.transform(entrada_test), columns=nombres, index=entrada_test.index)
    salida_train["returned"] = train["returned"].to_numpy()
    salida_test["returned"] = test["returned"].to_numpy()
    return salida_train, salida_test


def version_mal(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, ColumnTransformer]:
    """Recibe tabla completa; devuelve train/test preparados y un pipeline con filtración.

    Pista: reproduce a propósito el error de aprender la preparación antes de separar.
    """
    # Las funciones de la etapa 3 las completa el alumno; no se duplican aquí.
    from preparar.pipeline import construir_pipeline, separar

    pipeline = construir_pipeline()
    entrada = df.drop(columns="returned").set_index("order_id")
    pipeline.fit(entrada)  # Error didáctico: el examen participó de la mediana y la escala.
    preparada = pd.DataFrame(pipeline.transform(entrada), columns=pipeline.get_feature_names_out(), index=entrada.index)
    preparada["returned"] = df["returned"].to_numpy()
    train, test = separar(preparada)
    return train, test, pipeline

