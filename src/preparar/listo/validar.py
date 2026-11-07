# Rechaza valores imposibles y hace cumplir las reglas de descuento.
# Corresponde a la parte de la clase sobre validación y reglas de negocio.
"""Valores posibles y reglas de Tienda Nimbus."""
import pandas as pd

def validar(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe la tabla con tipos corregidos; devuelve filas válidas y cantidad rechazada.

    Pista: un precio desconocido se trata después; no es un precio imposible.
    """
    # Desconocido no significa imposible: los vacíos esperan a la etapa 3.
    precio_posible = df["price"].isna() | df["price"].gt(0)
    aceptada = precio_posible & df["quantity"].gt(0) & df["order_date"].notna()
    return df.loc[aceptada].copy(), int((~aceptada).sum())

def aplicar_reglas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recibe pedidos válidos; devuelve una copia con discount entre 0 y 1 y filas afectadas.

    Pista: las filas se conservan; solo se limita un valor fuera del intervalo.
    """
    resultado = df.copy()
    # En esta regla corregimos el descuento y conservamos la fila.
    fuera = ~resultado["discount"].between(0, 1)
    resultado["discount"] = resultado["discount"].clip(0, 1)
    return resultado, int(fuera.sum())
