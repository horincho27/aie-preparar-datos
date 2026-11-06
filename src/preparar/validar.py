"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def validar(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe la tabla con tipos corregidos; devuelve filas válidas y cantidad rechazada.
    
    Pista: un precio desconocido se trata después; no es un precio imposible."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def aplicar_reglas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe pedidos válidos; devuelve una copia con discount entre 0 y 1 y filas afectadas.
    
    Pista: las filas se conservan; solo se limita un valor fuera del intervalo."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
