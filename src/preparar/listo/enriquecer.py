# Calcula el precio por unidad sin arriesgar una división por cero.
# Corresponde a la parte de la clase sobre variables derivadas.
import pandas as pd

def precio_unitario(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe tabla; devuelve copia con precio_unitario, sin dividir por cero.

    Pista: un denominador no positivo debe dejar el resultado como faltante.
    """
    resultado = df.copy()
    # Un denominador no positivo deja un faltante en vez de infinito.
    resultado["precio_unitario"] = resultado["price"] / resultado["quantity"].where(resultado["quantity"].gt(0))
    return resultado

