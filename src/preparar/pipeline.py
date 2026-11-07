"""Completá estas funciones durante la clase de Tienda Nimbus."""

import pandas as pd
from sklearn.compose import ColumnTransformer

def separar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe tabla con returned; devuelve entrenamiento/prueba en proporción 80/20.
    
    Pista: conservá la proporción de la etiqueta y fijá random_state=42."""
    raise NotImplementedError("Completá esta función y verificá los tests de su etapa.")

def construir_pipeline() -> ColumnTransformer:
    """No recibe argumentos; devuelve un ColumnTransformer todavía sin ajustar.
    
    Pista: usá una rama numérica y otra categórica; admití categorías nuevas."""
    raise NotImplementedError("Completá esta función y verificá los tests de su etapa.")
