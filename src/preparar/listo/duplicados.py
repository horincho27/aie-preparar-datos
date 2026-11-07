# Quita copias exactas sin borrar compras legítimas con otro identificador.
# Corresponde a la parte de la clase sobre observaciones y duplicados.
"""Una observación por pedido, sin borrar compras legítimas."""
import pandas as pd

def eliminar_duplicados(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe una tabla; devuelve una copia sin filas exactas repetidas y su cantidad.

    Pista: dos order_id distintos representan observaciones distintas.
    """
    # Se comparan todas las columnas, incluido order_id.
    resultado = df.drop_duplicates().copy()
    return resultado, len(df) - len(resultado)
