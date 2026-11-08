"""Completa estas funciones durante la clase de Tienda Nimbus."""

import pandas as pd
from sklearn.compose import ColumnTransformer

def dias_desde_registro(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe pedidos con fechas; devuelve copia con dias_desde_registro.
    
    Pista: el reloj de esta cuenta es la fecha del pedido, no la fecha de hoy."""
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")

def quitar_filtracion(df: pd.DataFrame) -> pd.DataFrame:
    """quitar_filtracion(df) devuelve una copia sin las columnas que solo
    existen después de que el pedido se devolvió.
    
    Para encontrarlas, revisa cada columna de data/raw y pregúntate si
    existiría cuando llega un pedido nuevo. Debe funcionar aunque esas
    columnas ya falten, como ocurre en producción.
    """
    raise NotImplementedError("Completa esta función y ejecuta las pruebas de su etapa.")
