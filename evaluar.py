"""El modelo es fijo: aquí medimos la preparación, no elegimos algoritmos."""
from pathlib import Path
import base64
import json
import sys
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from preparar.listo.cargar import aplicar_a_nuevos
from preparar.listo.recorrido import comprobar_etapas
from preparar.listo.estado import EtapaPendiente

def main():
    # Detectamos primero la etapa pendiente, incluso si hay archivos de una ejecución vieja.
    comprobar_etapas()
    raiz = Path(__file__).resolve().parent
    carpeta = raiz / "data/processed"
    necesarios = [carpeta / nombre for nombre in ["train.csv", "test.csv", "preparacion.joblib", "esquema.json"]]
    if not all(ruta.exists() for ruta in necesarios):
        print("Falta generar los archivos de la etapa 3: ejecutá python run_all.py para crear data/processed.")
        return
    train = pd.read_csv(carpeta / "train.csv", index_col="order_id")
    test = pd.read_csv(carpeta / "test.csv", index_col="order_id")
    columnas = train.columns.drop("returned")
    # Este modelo y sus parámetros se mantienen iguales para toda la clase.
    modelo = LogisticRegression(max_iter=1000, random_state=42)
    modelo.fit(train[columnas], train["returned"])
    nuevos = aplicar_a_nuevos(raiz / "data/new/orders_new.csv")
    pedidos = pd.read_csv(raiz / "data/new/orders_new.csv")
    respuestas = json.loads(base64.b64decode((raiz / "data/new/.respuestas").read_bytes()).decode("utf-8"))
    if len(respuestas) != len(pedidos):
        raise ValueError("Las respuestas no corresponden a los pedidos de producción.")
    etiquetas = pd.Series(respuestas, index=pedidos["order_id"])
    if not etiquetas.index.is_unique:
        if etiquetas.groupby(level=0).nunique().gt(1).any():
            raise ValueError("Un pedido repetido tiene respuestas distintas.")
        etiquetas = etiquetas[~etiquetas.index.duplicated()]
    # La limpieza puede rechazar filas: se comparan por identificador, no por posición.
    conjuntos = [("Tu prueba", test[columnas], test["returned"]), ("Producción", nuevos[columnas], etiquetas.loc[nuevos.index])]
    print(f"{'Conjunto':<14} {'F1':>6}   {'Devoluciones detectadas':<25} {'Exactitud':>10}")
    puntajes = {}
    for nombre, entrada, reales in conjuntos:
        predichas = modelo.predict(entrada)
        puntaje = f1_score(reales, predichas, zero_division=0)
        detectadas = int(((predichas == 1) & (reales.to_numpy() == 1)).sum())
        total = int(reales.sum())
        exactitud = accuracy_score(reales, predichas)
        puntajes[nombre] = puntaje
        print(f"{nombre:<14} {puntaje:>6.3f}   {str(detectadas) + ' de ' + str(total):<25} {exactitud:>9.1%}")
    registro = nuevos.attrs["registro"]
    print(f"Producción: {registro['leidas']} filas leídas, {registro['duplicadas']} duplicadas, {registro['rechazadas']} rechazadas y {registro['procesadas']} evaluadas.")
    print("La exactitud sola engaña: decir 'nadie devuelve' ya acierta alrededor del 80 %, pero no detecta ninguna devolución.")
    if puntajes["Tu prueba"] - puntajes["Producción"] > 0.15:
        print("Tu prueba da mucho mejor que producción. Revisá la etapa 2: puede haber quedado información del futuro.")
    print(f"Mi F1 en producción: {puntajes['Producción']:.2f}".replace(".", ","))

if __name__ == "__main__":
    try:
        main()
    except EtapaPendiente as error:
        print(error)
    except FileNotFoundError:
        print("Faltan archivos: revisá data/raw, data/new y data/processed y ejecutá python run_all.py.")
    except (ValueError, KeyError):
        print("Los archivos preparados no coinciden con lo esperado. Revisá las etapas 2 y 3 y volvé a ejecutar python run_all.py.")
