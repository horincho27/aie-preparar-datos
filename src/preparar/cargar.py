"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def guardar(train: pd.DataFrame, test: pd.DataFrame, pipeline: ColumnTransformer, destino: str | Path | None = None) -> None:
    """Recibe tablas preparadas y pipeline ajustado; escribe CSV, joblib y esquema JSON.
    
    Pista: guardá también las columnas de entrada, sus tipos y una fecha UTC."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def preparar_crudos(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Recibe pedidos y clientes; devuelve la tabla de etapas 3 a 7 y un registro de filas.
    
    Pista: reutilizá las funciones anteriores, en el mismo orden que run_all.py."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def aplicar_a_nuevos(path: str | Path, artefactos: str | Path | None = None) -> pd.DataFrame:
    """Recibe CSV de pedidos nuevos; devuelve características con columnas iguales a train.
    
    Pista: cargá el joblib y usá transform; conservá order_id para alinear respuestas.
    El registro de filas queda en resultado.attrs['registro']."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
