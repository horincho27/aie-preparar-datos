"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def informe(df: pd.DataFrame) -> dict:
    """Recibe una tabla; devuelve filas, nulos, duplicados, tipos y tasa_devolucion.
    
    Pista: pandas puede contar ausencias y comparar filas completas."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
