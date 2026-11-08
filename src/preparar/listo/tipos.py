# Convierte las distintas escrituras de precios, fechas y categorías.
# Corresponde a la parte de la clase sobre tipos y formatos.
"""Los mismos valores deben tener una sola representación."""
import pandas as pd

def convertir_precio(serie: pd.Series) -> pd.Series:
    """Recibe precios de texto; devuelve una serie numérica conservando los vacíos.

    Pista: la coma puede representar miles o decimales según el formato.
    """
    texto = serie.astype("string").str.strip()
    con_moneda = texto.str.contains("$", regex=False, na=False)
    # El signo $ identifica el formato que trae coma de miles.
    texto.loc[con_moneda] = texto.loc[con_moneda].str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    texto.loc[~con_moneda] = texto.loc[~con_moneda].str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce").astype(float)

def convertir_fecha(serie: pd.Series) -> pd.Series:
    """Recibe fechas de texto; devuelve datetime y NaT para fechas ilegibles.

    Pista: prueba los dos formatos explícitos para evitar ambigüedades de día y mes.
    """
    # Dos formatos explícitos evitan confundir el día con el mes.
    principal = pd.to_datetime(serie, format="%Y-%m-%d", errors="coerce")
    secundario = pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce")
    return principal.fillna(secundario)

def estandarizar_categoria(serie: pd.Series) -> pd.Series:
    """Recibe categorías de texto; devuelve sus nombres en una forma uniforme.

    Pista: revisa mayúsculas y espacios al principio o al final.
    """
    # La misma categoría no debe separarse por espacios o mayúsculas.
    return serie.astype("string").str.strip().str.lower()
