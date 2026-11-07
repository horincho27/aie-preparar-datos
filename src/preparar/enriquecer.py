"""Completá estas funciones durante la clase de Tienda Nimbus."""

import pandas as pd
from sklearn.compose import ColumnTransformer

def dias_desde_registro(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe pedidos con fechas; devuelve copia con dias_desde_registro.
    
    Pista: el reloj de esta cuenta es la fecha del pedido, no la fecha de hoy."""
    raise NotImplementedError("Completá esta función y verificá los tests de su etapa.")

def quitar_filtracion(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe tabla; devuelve copia sin refund_amount ni return_reason.
    
    Pista: pensá si esas columnas existirían al llegar un pedido nuevo."""
    raise NotImplementedError("Completá esta función y verificá los tests de su etapa.")
