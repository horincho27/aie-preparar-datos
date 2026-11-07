# Mide el estado de la tabla antes de corregirla.
# Corresponde a la parte de la clase sobre exploración y calidad de datos.
"""Mediciones antes de decidir una limpieza."""
import pandas as pd

def informe(df: pd.DataFrame) -> dict:
    """Recibe una tabla; devuelve filas, nulos, duplicados, tipos y tasa_devolucion.

    Pista: pandas puede contar ausencias y comparar filas completas.
    """
    # Contamos sin modificar la tabla; la media de 0/1 es una proporción.
    return {
        "filas": len(df),
        "nulos": df.isna().sum().astype(int).to_dict(),
        "duplicados_exactos": int(df.duplicated().sum()),
        "tipos": df.dtypes.astype(str).to_dict(),
        "tasa_devolucion": float(df["returned"].mean()),
    }
