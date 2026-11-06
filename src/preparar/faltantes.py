"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def agregar_indicador_faltante(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Recibe tabla y nombre de columna; devuelve copia con <columna>_missing de 0/1.
    
    Pista: medí la ausencia antes de cualquier relleno."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def comparar_tasa(df: pd.DataFrame, indicador: str) -> dict[int, float]:
    """Recibe tabla etiquetada e indicador; devuelve la tasa de returned por grupo.
    
    Pista: una media de ceros y unos es una proporción."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
