# Lee los archivos locales y junta pedidos con clientes sin perder filas.
# Corresponde a la parte de la clase sobre fuentes de datos y uniones.
"""Lectura local y unión de las dos fuentes."""
from pathlib import Path
import pandas as pd

def cargar_fuentes(base: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recibe la raíz opcional del proyecto y devuelve pedidos y clientes.

    Pista: son dos formatos de archivo distintos dentro de data/raw.
    """
    raiz = Path(base) if base is not None else Path(__file__).resolve().parents[3]
    # El precio se conserva como texto: todavía hay formatos mezclados.
    pedidos = pd.read_csv(raiz / "data/raw/orders.csv", dtype={"price": "string"})
    clientes = pd.read_json(raiz / "data/raw/customers.json", convert_dates=False)
    return pedidos, clientes

def unir(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Recibe pedidos y clientes; devuelve la unión y las cantidades antes/después.

    Pista: cada pedido debe conservarse aunque no encuentre un cliente.
    """
    # many_to_one evita que un cliente repetido multiplique los pedidos.
    tabla = orders.merge(customers, on="customer_id", how="left", validate="many_to_one")
    registro = {"antes": len(orders), "despues": len(tabla)}
    return tabla, registro
