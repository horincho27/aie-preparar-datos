"""Completa estas funciones durante la clase de Tienda Nimbus."""

import pandas as pd
from sklearn.compose import ColumnTransformer

def separar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe tabla con returned; devuelve entrenamiento/prueba en proporción 80/20.
    
    Pista: conserva la proporción de la etiqueta y fija random_state=42."""
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")

def construir_pipeline() -> ColumnTransformer:
    """No recibe argumentos; devuelve un ColumnTransformer todavía sin ajustar.
    
    Pista: usa una rama numérica y otra categórica. Admite categorías nuevas."""
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")
