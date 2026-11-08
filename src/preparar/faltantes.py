"""Completa estas funciones durante la clase de Tienda Nimbus."""

import pandas as pd
from sklearn.compose import ColumnTransformer

def agregar_indicador_faltante(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Recibe tabla y nombre de columna; devuelve copia con <columna>_missing de 0/1.
    
    Pista: mide la ausencia antes de cualquier relleno."""
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")

def comparar_tasa(df: pd.DataFrame, columna: str) -> dict[int, float]:
    """Recibe tabla etiquetada e indicador; devuelve la tasa de returned por grupo.
    
    Pista: una media de ceros y unos es una proporción."""
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")
