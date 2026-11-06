"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def convertir_precio(serie: pd.Series) -> pd.Series:
    """Recibe precios de texto; devuelve una serie numérica conservando los vacíos.
    
    Pista: la coma puede representar miles o decimales según el formato."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def convertir_fecha(serie: pd.Series) -> pd.Series:
    """Recibe fechas de texto; devuelve datetime y NaT para fechas ilegibles.
    
    Pista: probá los dos formatos explícitos para evitar ambigüedades de día y mes."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def estandarizar_categoria(serie: pd.Series) -> pd.Series:
    """Recibe categorías de texto; devuelve sus nombres en una forma uniforme.
    
    Pista: revisá mayúsculas y espacios al principio o al final."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
