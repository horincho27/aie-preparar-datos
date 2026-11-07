# Guarda la preparación y aplica el mismo recorrido a pedidos de producción.
# Corresponde a la parte de la clase sobre carga, persistencia e inferencia.
"""Persistencia y reutilización de la preparación en pedidos nuevos."""
from datetime import datetime, timezone
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from preparar.listo.extraer import cargar_fuentes, unir
from preparar.listo.duplicados import eliminar_duplicados
from preparar.listo.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from preparar.listo.validar import validar, aplicar_reglas
from preparar.faltantes import agregar_indicador_faltante
from preparar.enriquecer import dias_desde_registro, quitar_filtracion
from preparar.listo.enriquecer import precio_unitario
from preparar.listo.estado import ejecutar_etapa

def guardar(train: pd.DataFrame, test: pd.DataFrame, pipeline: ColumnTransformer, destino: str | Path | None = None) -> None:
    """Recibe tablas preparadas y pipeline ajustado; escribe CSV, joblib y esquema JSON.

    Pista: guardá también las columnas de entrada, sus tipos y una fecha UTC.
    """
    carpeta = Path(destino) if destino is not None else Path(__file__).resolve().parents[3] / "data/processed"
    carpeta.mkdir(parents=True, exist_ok=True)
    train.to_csv(carpeta / "train.csv", index_label="order_id")
    test.to_csv(carpeta / "test.csv", index_label="order_id")
    joblib.dump(pipeline, carpeta / "preparacion.joblib")
    esquema = {"columnas_entrada": pipeline.feature_names_in_.tolist(), "tipos": pipeline.tipos_entrada_, "fecha": datetime.now(timezone.utc).isoformat(), "columnas_salida": pipeline.get_feature_names_out().tolist()}
    (carpeta / "esquema.json").write_text(json.dumps(esquema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def preparar_base(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Recibe pedidos y clientes; devuelve limpieza inicial y registro de filas.

    Esta parte ya está resuelta; conserva price vacío para la etapa 3.
    """
    tabla, union = unir(orders, customers)
    tabla, duplicados = eliminar_duplicados(tabla)
    tabla["price"] = convertir_precio(tabla["price"])
    tabla["order_date"] = convertir_fecha(tabla["order_date"])
    tabla["category"] = estandarizar_categoria(tabla["category"])
    tabla, rechazadas = validar(tabla)
    tabla, limitadas = aplicar_reglas(tabla)
    registro = {"leidas": len(orders), "unidas": union["despues"], "duplicadas": duplicados, "rechazadas": rechazadas, "descuentos_limitados": limitadas, "procesadas": len(tabla)}
    return tabla, registro


def preparar_crudos(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Recibe fuentes; devuelve la base más las etapas 1 y 2, y un registro.

    Se reutiliza exactamente este recorrido al preparar pedidos nuevos.
    """
    tabla, registro = preparar_base(orders, customers)
    tabla = ejecutar_etapa(1, agregar_indicador_faltante, tabla, "phone")
    tabla = ejecutar_etapa(2, dias_desde_registro, tabla)
    tabla = precio_unitario(tabla)
    tabla = ejecutar_etapa(2, quitar_filtracion, tabla)
    return tabla, registro


def aplicar_a_nuevos(path: str | Path, artefactos: str | Path | None = None) -> pd.DataFrame:
    """Recibe CSV de pedidos nuevos; devuelve características con columnas iguales a train.

    Pista: cargá el joblib y usá transform; conservá order_id para alinear respuestas.
    El registro de filas queda en resultado.attrs['registro'].
    """
    ruta = Path(path)
    raiz = ruta.resolve().parents[2]
    carpeta = Path(artefactos) if artefactos is not None else raiz / "data/processed"
    pipeline = joblib.load(carpeta / "preparacion.joblib")
    _, clientes = cargar_fuentes(raiz)
    nuevos = pd.read_csv(ruta, dtype={"price": "string"})
    # La limpieza y las etapas del alumno son las mismas que en entrenamiento.
    tabla, registro = preparar_crudos(nuevos, clientes)
    entrada = tabla.set_index("order_id")
    # El esquema conserva columnas descartadas por el transformador. No se inventan
    # valores para columnas que el modelo realmente usa: el experimento con fuga
    # debe declarar explícitamente cómo representa el futuro ausente.
    faltantes = set(pipeline.feature_names_in_) - set(entrada.columns)
    usadas = set()
    for _, transformador, columnas in pipeline.transformers_:
        if not isinstance(transformador, str):
            usadas.update(columnas)
    permitidas = set(getattr(pipeline, "permitir_ausentes_", []))
    if (faltantes & usadas) - permitidas:
        raise ValueError("Faltan características necesarias para la preparación guardada.")
    entrada = entrada.reindex(columns=pipeline.feature_names_in_)
    for columna in permitidas:
        if columna == "return_reason":
            entrada[columna] = entrada[columna].astype(object)
    # Solo transform: la mediana y la escala ya se aprendieron con train.
    resultado = pd.DataFrame(pipeline.transform(entrada), columns=pipeline.get_feature_names_out(), index=entrada.index)
    resultado.attrs["registro"] = registro
    return resultado
