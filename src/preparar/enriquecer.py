"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def dias_desde_registro(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe pedidos con fechas; devuelve copia con dias_desde_registro.
    
    Pista: el reloj de esta cuenta es la fecha del pedido, no la fecha de hoy."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def precio_unitario(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe tabla; devuelve copia con precio_unitario, sin dividir por cero.
    
    Pista: un denominador no positivo debe dejar el resultado como faltante."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def quitar_filtracion(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe tabla; devuelve copia sin refund_amount ni return_reason.
    
    Pista: pensá si esas columnas existirían al llegar un pedido nuevo."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
