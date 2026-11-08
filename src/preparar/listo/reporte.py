# Mide una etapa a la vez con la misma preparación de referencia en las demás.
# Los valores de listo permiten evaluar un avance aunque falten otras etapas.
from pathlib import Path
import base64
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from preparar import enriquecer, faltantes, pipeline as etapa_pipeline
from preparar.listo.cargar import preparar_base, transformar_pedidos
from preparar.listo.enriquecer import precio_unitario
from preparar.listo.estado import ejecutar_etapa, EtapaPendiente
from preparar.listo.extraer import cargar_fuentes
from preparar.listo.pipeline import ajustar_y_transformar, version_mal

FUTURAS = ["refund_amount", "return_reason"]


def decimal(valor, cifras=3):
    return f"{valor:.{cifras}f}".replace(".", ",")


def porcentaje(valor):
    return f"{decimal(100 * valor, 2)} %"


def metricas(reales, predichas):
    return {
        "f1": f1_score(reales, predichas, zero_division=0),
        "detectadas": f"{int(((predichas == 1) & (reales == 1)).sum())} de {int(reales.sum())}",
        "exactitud": accuracy_score(reales, predichas),
    }


def con_filtracion(pipeline):
    """Añade explícitamente las dos columnas que aparecen después del pedido."""
    futuro_numerico = SimpleImputer(strategy="constant", fill_value=0)
    futuro_texto = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="sin_devolucion")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    variante = clone(pipeline)
    variante.set_params(transformers=[
        *variante.transformers,
        ("reembolso_futuro", futuro_numerico, ["refund_amount"]),
        ("motivo_futuro", futuro_texto, ["return_reason"]),
    ])
    # Esos campos no existen cuando llega un pedido nuevo. Se tratan como vacíos.
    variante.permitir_ausentes_ = FUTURAS
    return variante


def mediana_aprendida(pipeline):
    imputador = pipeline.named_transformers_["numericas"].named_steps["imputer"]
    posicion = list(imputador.feature_names_in_).index("price")
    return imputador.statistics_[posicion]


class Evaluacion:
    def __init__(self, raiz):
        pedidos, clientes = cargar_fuentes(raiz)
        nuevos = pd.read_csv(raiz / "data/new/orders_new.csv", dtype={"price": "string"})
        self.historico = precio_unitario(preparar_base(pedidos, clientes)[0])
        self.nuevos = precio_unitario(preparar_base(nuevos, clientes)[0])
        respuestas = json.loads(base64.b64decode((raiz / "data/new/.respuestas").read_bytes()))
        self.etiquetas = pd.Series(respuestas, index=nuevos["order_id"])
        if self.etiquetas.groupby(level=0).nunique().gt(1).any():
            raise ValueError("Un pedido repetido tiene respuestas distintas.")
        self.etiquetas = self.etiquetas[~self.etiquetas.index.duplicated()]
        self.referencia = joblib.load(Path(__file__).with_name("referencia_evaluacion.joblib"))

    def agregar_referencia(self, tabla, *columnas):
        valores = self.referencia["derivadas"].loc[tabla["order_id"], list(columnas)]
        return tabla.assign(**{columna: valores[columna].to_numpy() for columna in columnas})

    def separar_referencia(self, tabla):
        por_pedido = tabla.set_index("order_id", drop=False)
        return tuple(por_pedido.loc[ids] for ids in self.referencia["particiones"])

    def puntuar(self, train, test, nuevos, pipeline):
        # Se entrena el mismo modelo en cada comparación. Producción usa solo transform.
        modelo = LogisticRegression(max_iter=1000, random_state=42)
        modelo.fit(train.drop(columns="returned"), train["returned"])
        produccion = transformar_pedidos(nuevos, pipeline)
        return (
            metricas(test["returned"], modelo.predict(test.drop(columns="returned"))),
            metricas(self.etiquetas.loc[produccion.index], modelo.predict(produccion)),
        )

    def medir(self, partes, nuevos, pipeline):
        train, test = ajustar_y_transformar(*partes, pipeline)
        return self.puntuar(train, test, nuevos, pipeline)

    def etapa_1(self):
        # Las dos pruebas excluyen los datos futuros y usan los mismos pedidos.
        historico = self.agregar_referencia(self.historico.drop(columns=FUTURAS), "dias_desde_registro")
        nuevos = self.agregar_referencia(self.nuevos, "dias_desde_registro")
        despues = ejecutar_etapa(1, faltantes.agregar_indicador_faltante, historico.copy(), "phone")
        tasas = ejecutar_etapa(1, faltantes.comparar_tasa, despues.copy(), "phone_missing")
        despues_nuevos = ejecutar_etapa(1, faltantes.agregar_indicador_faltante, nuevos.copy(), "phone")
        indicadores = tuple(
            tabla.set_index("order_id")["phone_missing"] for tabla in (despues, despues_nuevos)
        )

        con_indicador = clone(self.referencia["pipeline"])
        sin_indicador = clone(con_indicador)
        sin_indicador.set_params(transformers=[
            (nombre, paso, [columna for columna in columnas if columna != "phone_missing"])
            for nombre, paso, columnas in sin_indicador.transformers
        ])
        f1_antes = self.medir(self.separar_referencia(historico), nuevos, sin_indicador)[1]["f1"]
        f1_despues = self.medir(
            self.separar_referencia(historico.join(indicadores[0], on="order_id")),
            nuevos.join(indicadores[1], on="order_id"),
            con_indicador,
        )[1]["f1"]
        return [
            "Etapa 1 · El dato que falta",
            "Qué hiciste · Marcaste los pedidos sin teléfono y comparaste las tasas de devolución.",
            f"Tasas de devolución · Con teléfono {porcentaje(tasas[0])}, sin teléfono {porcentaje(tasas[1])}.",
            f"Antes · F1 en producción sin el indicador {decimal(f1_antes)}.",
            f"Después · F1 en producción con el indicador {decimal(f1_despues)}.",
            "Qué significa · El indicador permite que el modelo use la diferencia entre los dos grupos.",
        ], indicadores

    def etapa_2(self):
        base = self.agregar_referencia(self.historico, "phone_missing")
        nuevos = self.agregar_referencia(self.nuevos, "phone_missing")
        antes = ejecutar_etapa(2, enriquecer.dias_desde_registro, base.copy())
        repeticion = ejecutar_etapa(2, enriquecer.dias_desde_registro, base.copy())
        coinciden = antes["dias_desde_registro"].equals(repeticion["dias_desde_registro"])
        despues = ejecutar_etapa(2, enriquecer.quitar_filtracion, antes.copy())
        nuevos = ejecutar_etapa(2, enriquecer.dias_desde_registro, nuevos)
        nuevos = ejecutar_etapa(2, enriquecer.quitar_filtracion, nuevos)
        if set(FUTURAS).intersection(despues.columns):
            raise ValueError("Todavía hay datos posteriores al pedido.")

        referencia = self.referencia["pipeline"]
        prueba_antes, produccion_antes = self.medir(
            self.separar_referencia(antes), nuevos, con_filtracion(referencia)
        )
        prueba_despues, produccion_despues = self.medir(
            self.separar_referencia(despues), nuevos, clone(referencia)
        )
        return [
            "Etapa 2 · La columna que hace trampa",
            "Qué hiciste · Calculaste los días desde el registro y quitaste el monto y el motivo de devolución.",
            f"Antes · Con los datos futuros, F1 en prueba {decimal(prueba_antes['f1'])} y en producción {decimal(produccion_antes['f1'])}.",
            f"Después · Sin los datos futuros, F1 en prueba {decimal(prueba_despues['f1'])} y en producción {decimal(produccion_despues['f1'])}.",
            f"Días desde el registro · Dos cálculos sobre {len(base)} pedidos dieron {'el mismo resultado exacto' if coinciden else 'resultados distintos'}.",
            "Qué significa · El reembolso adelanta la respuesta en la prueba, pero aún no existe cuando llega un pedido nuevo.",
        ], (despues, nuevos)

    def etapa_3(self):
        columnas = ("phone_missing", "dias_desde_registro")
        historico = self.agregar_referencia(self.historico.drop(columns=FUTURAS), *columnas)
        nuevos = self.agregar_referencia(self.nuevos, *columnas)
        partes = ejecutar_etapa(3, etapa_pipeline.separar, historico.copy())
        pipeline = ejecutar_etapa(3, etapa_pipeline.construir_pipeline)
        prueba, produccion = self.medir(partes, nuevos, pipeline)
        train_mal, test_mal, pipeline_mal = ejecutar_etapa(3, version_mal, historico, particiones=partes)
        prueba_mal, produccion_mal = self.puntuar(train_mal, test_mal, nuevos, pipeline_mal)
        diferencia_prueba = prueba_mal["f1"] - prueba["f1"]
        diferencia_produccion = produccion_mal["f1"] - produccion["f1"]
        diferencia_maxima = max(abs(diferencia_prueba), abs(diferencia_produccion))
        if diferencia_maxima == 0:
            cambio = "no cambió el F1"
        elif diferencia_maxima < 0.01:
            cambio = "casi no cambió el F1 (diferencias menores que 0,01)"
        else:
            cambio = "cambió el F1"
        train, test = partes
        mediana_total = decimal(historico["price"].median(), 2)
        return [
            "Etapa 3 · Separar y preparar sin filtración",
            "Qué hiciste · Separaste los pedidos y ajustaste la preparación solo con los de entrenamiento.",
            f"Si ajustaras con todo · {len(historico)} de {len(historico)} pedidos. Mediana aprendida {decimal(mediana_aprendida(pipeline_mal), 2)}. F1 en prueba {decimal(prueba_mal['f1'])} y en producción {decimal(produccion_mal['f1'])}.",
            f"Tu ajuste · {len(train)} de {len(historico)} pedidos. Mediana aprendida {decimal(mediana_aprendida(pipeline), 2)} frente a {mediana_total} en el total. F1 en prueba {decimal(prueba['f1'])} y en producción {decimal(produccion['f1'])}.",
            f"Devoluciones · Entrenamiento {porcentaje(train['returned'].mean())} ({int(train['returned'].sum())} de {len(train)}). Prueba {porcentaje(test['returned'].mean())} ({int(test['returned'].sum())} de {len(test)}).",
            f"Producción · {len(nuevos)} pedidos transformados sin volver a ajustar.",
            f"Diferencia de F1 (ajuste con todo menos ajuste con entrenamiento) · Prueba {decimal(diferencia_prueba)}, producción {decimal(diferencia_produccion)}.",
            f"Qué significa · En esta comparación, ajustar con todo {cambio}. Ese ajuste incluye los pedidos de prueba y compromete la evaluación.",
        ], None

    def cierre(self, indicadores, tablas):
        # La tabla final combina las tres etapas del alumno y compara los mismos pedidos.
        historico, nuevos = (
            tabla.drop(columns="phone_missing").join(indicador, on="order_id")
            for tabla, indicador in zip(tablas, indicadores)
        )
        partes = etapa_pipeline.separar(historico)
        pipeline = etapa_pipeline.construir_pipeline()
        correcta = self.medir(partes, nuevos, pipeline)
        futuro = self.historico.set_index("order_id")[FUTURAS]
        partes_con_futuro = tuple(parte.join(futuro, on="order_id") for parte in partes)
        filtracion = self.medir(partes_con_futuro, nuevos, con_filtracion(pipeline))
        reales = self.etiquetas.loc[nuevos["order_id"]]
        cero = (None, metricas(reales, np.zeros(len(reales), dtype=int)))
        imprimir_cierre(correcta, filtracion, cero)


def imprimir_cierre(correcta, filtracion, cero):
    formato = "{:<20} {:>9} {:>13} {:>17} {:>21} {:>16} {:>20}"
    print("Comparación final")
    print(formato.format(
        "Preparación", "F1 prueba", "F1 producción", "Detectadas prueba",
        "Detectadas producción", "Exactitud prueba", "Exactitud producción",
    ))
    for nombre, (prueba, produccion) in zip(
        ("Correcta", "Con datos del futuro", "Siempre cero"), (correcta, filtracion, cero)
    ):
        f1_prueba = decimal(prueba["f1"]) if prueba else "—"
        detectadas_prueba = prueba["detectadas"] if prueba else "—"
        exactitud_prueba = porcentaje(prueba["exactitud"]) if prueba else "—"
        print(formato.format(
            nombre, f1_prueba, decimal(produccion["f1"]), detectadas_prueba,
            produccion["detectadas"], exactitud_prueba, porcentaje(produccion["exactitud"]),
        ))
    print("La exactitud cuenta todos los aciertos. Predecir cero en cada pedido acierta muchos casos y no detecta ninguna devolución.")
    print(f"Mi F1 en producción: {decimal(correcta[1]['f1'], 2)}")


def mostrar_reportes(raiz):
    evaluacion = Evaluacion(raiz)
    pendientes = []
    completas = {}
    for numero, etapa in enumerate((evaluacion.etapa_1, evaluacion.etapa_2, evaluacion.etapa_3), 1):
        try:
            lineas, completas[numero] = etapa()
        except EtapaPendiente as error:
            pendientes.append(error)
        except (AttributeError, KeyError, TypeError, ValueError):
            print(f"Revisa la etapa {numero}. Ejecuta sus pruebas para localizar el problema.")
        else:
            print("\n".join(lineas))
            print()
    if pendientes:
        print(pendientes[0])
    if len(completas) == 3:
        evaluacion.cierre(completas[1], completas[2])
