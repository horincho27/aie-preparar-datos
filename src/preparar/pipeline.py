"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def separar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe tabla con returned; devuelve entrenamiento/prueba en proporción 80/20.
    
    Pista: conservá la proporción de la etiqueta y fijá random_state=42."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def construir_pipeline() -> ColumnTransformer:
    """No recibe argumentos; devuelve un ColumnTransformer todavía sin ajustar.
    
    Pista: usá una rama numérica y otra categórica; admití categorías nuevas."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def ajustar_y_transformar(train: pd.DataFrame, test: pd.DataFrame, pipeline: ColumnTransformer) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe particiones crudas y pipeline; devuelve tablas numéricas con returned.
    
    Pista: el ajuste ocurre una vez y solo ve train; usá order_id como índice."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def version_mal(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, ColumnTransformer]:
    """Recibe tabla completa; devuelve train/test preparados y un pipeline con filtración.
    
    Pista: reproduce a propósito el error de aprender la preparación antes de separar."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
