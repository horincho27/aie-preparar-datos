"""Funciones para resolver durante la clase de Tienda Nimbus."""

from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer

def cargar_fuentes(base: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe la raíz opcional del proyecto y devuelve pedidos y clientes.
    
    Pista: son dos formatos de archivo distintos dentro de data/raw."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")

def unir(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Recibe pedidos y clientes; devuelve la unión y las cantidades antes/después.
    
    Pista: cada pedido debe conservarse aunque no encuentre un cliente."""
    raise NotImplementedError("Completá esta función en la etapa indicada.")
