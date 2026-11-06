"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def eliminar_duplicados(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe una tabla; devuelve una copia sin filas exactas repetidas y su cantidad.
    
    Pista: dos order_id distintos representan observaciones distintas."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
