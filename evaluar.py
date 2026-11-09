"""Comprueba lo que quedó preparado en la última medición."""

import argparse
from math import ceil

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone

from medir import (
    PREPARACION, ULTIMA, _entradas, _revisar_matriz, cargar_datos,
    campos_exclusivos, leer_historial,
)


class FaltaEtapa(ValueError):
    """Una condición de la etapa que todavía no se cumple."""


def _comprueba(condicion, mensaje):
    if not condicion:
        raise FaltaEtapa(mensaje)


def _limpieza(tabla, nombre):
    columnas = {"price", "order_date", "category", "quantity", "discount"}
    _comprueba(columnas.issubset(tabla.columns), f"Conserva las columnas de limpieza en {nombre}.")
    _comprueba(not tabla.duplicated().any() and tabla["order_id"].is_unique,
               f"Revisa los duplicados en {nombre}. Conserva las compras con otro identificador.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["price"]), f"Convierte price a número en {nombre}.")
    _comprueba(pd.api.types.is_datetime64_any_dtype(tabla["order_date"]),
               f"Convierte order_date a fecha en {nombre}.")
    _comprueba(tabla["order_date"].notna().all(), f"Quita las fechas ilegibles de {nombre}.")
    precios_conocidos = tabla["price"].dropna()
    _comprueba(np.isfinite(precios_conocidos).all() and precios_conocidos.gt(0).all(),
               f"Quita los precios imposibles de {nombre}. Los precios vacíos pueden esperar.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["quantity"]) and tabla["quantity"].gt(0).all(),
               f"Revisa las cantidades en {nombre}.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["discount"]) and tabla["discount"].between(0, 1).all(),
               f"Deja discount entre 0 y 1 en {nombre}.")
    categorias = tabla["category"].astype("string")
    _comprueba(categorias.notna().all() and categorias.ne("").all()
               and categorias.eq(categorias.str.strip().str.lower()).all(),
               f"Unifica category en {nombre} con minúsculas y sin espacios en los bordes.")


def _por_pedido(crudo, columna, tabla):
    valores = crudo.drop_duplicates("order_id").set_index("order_id")[columna]
    return tabla["order_id"].map(valores)


def _etapa_1(info, crudo, crudos_nuevos):
    _limpieza(info["historico"], "el histórico")
    _limpieza(info["nuevos"], "producción")
    salieron = len(crudo) - len(info["historico"])
    salieron_nuevos = len(crudos_nuevos) - len(info["nuevos"])
    return f"Limpieza correcta. Salieron {salieron} filas del histórico y {salieron_nuevos} de producción."


def _etapa_2(info, crudo, crudos_nuevos):
    for tabla, original in ((info["historico"], crudo), (info["nuevos"], crudos_nuevos)):
        _comprueba("phone_missing" in tabla, "Crea phone_missing en las dos tablas.")
        indicador = tabla["phone_missing"]
        esperado = _por_pedido(original, "phone", tabla).isna().astype(int)
        _comprueba(indicador.isin([0, 1]).all() and indicador.eq(esperado).all(),
                   "Usa 1 cuando falta el teléfono y 0 cuando está presente.")
    tasas = info["historico"].groupby("phone_missing")["returned"].mean()
    _comprueba({0, 1}.issubset(tasas.index), "Conserva pedidos de ambos grupos para comparar sus tasas.")
    con = f"{100 * tasas[0]:.2f}".replace(".", ",")
    sin = f"{100 * tasas[1]:.2f}".replace(".", ",")
    return f"Indicador correcto. Devoluciones con teléfono {con} %, sin teléfono {sin} %."


def _etapa_3(info, crudo, crudos_nuevos):
    exclusivas = campos_exclusivos(crudo, crudos_nuevos)
    for tabla, original in ((info["historico"], crudo), (info["nuevos"], crudos_nuevos)):
        _comprueba("dias_desde_registro" in tabla, "Crea dias_desde_registro en las dos tablas.")
        registro = pd.to_datetime(_por_pedido(original, "signup_date", tabla), format="%Y-%m-%d")
        esperados = (tabla["order_date"] - registro).dt.days
        _comprueba(tabla["dias_desde_registro"].eq(esperados).all(),
                   "Calcula los días entre el registro y la fecha del pedido.")
        _comprueba(set(exclusivas).isdisjoint(tabla.columns),
                   "Revisa qué campos solo existen después de la devolución.")
    _comprueba(info["repetible"] is not None, "Vuelve a medir con etapa=3 para comprobar el resultado.")
    _comprueba(info["repetible"], "Prepara dos veces los mismos pedidos y obtén el mismo resultado.")
    _comprueba(info["sin_futuro"], "Evita que la preparación dependa de información posterior al pedido.")
    return "Días reproducibles y preparación sin datos del futuro."


def _etapa_4(info, crudo, crudos_nuevos):
    historico = info["historico"]
    ids_train, ids_prueba = info["ids_train"], info["ids_prueba"]
    train_ids, prueba_ids = set(ids_train), set(ids_prueba)
    _comprueba(train_ids.isdisjoint(prueba_ids)
               and train_ids | prueba_ids == set(historico["order_id"])
               and len(prueba_ids) == ceil(len(historico) * 0.2),
               "Separa 80/20 sin compartir identificadores entre train y prueba.")
    train, prueba, nuevos, y_train, y_prueba = _entradas(
        historico, info["nuevos"], ids_train, ids_prueba
    )
    _comprueba(abs(y_train.mean() - y_prueba.mean()) <= 1 / len(prueba) + 1 / len(train),
               "Estratifica por returned para conservar proporciones parecidas.")
    evidencia = info["ajuste"]
    _comprueba(evidencia is not None and PREPARACION.is_file(),
               "Pasa un transformador sin ajustar a medir para guardar la preparación.")
    ajuste = joblib.load(PREPARACION)
    estado = evidencia["estado"]
    _comprueba(evidencia["ids"] == ids_train and joblib.hash(ajuste) == estado,
               "Vuelve a medir para guardar el ajuste que corresponde a train.")
    # Una copia nueva aprende solo de train. Comparamos su estado aprendido con el guardado.
    referencia = clone(ajuste).fit(train)
    _comprueba(joblib.hash(referencia) == estado,
               "Revisa que el transformador aprenda solo de train y use una semilla fija si la necesita.")
    _revisar_matriz(ajuste.transform(prueba), "prueba")
    _revisar_matriz(ajuste.transform(nuevos), "producción")
    _comprueba(joblib.hash(ajuste) == estado, "Usa transform sin cambiar el ajuste guardado.")
    categorias_originales = crudo["category"].str.strip().str.lower()
    categorias_nuevas = crudos_nuevos["category"].str.strip().str.lower()
    pedidos_nuevos = crudos_nuevos.loc[~categorias_nuevas.isin(categorias_originales), "order_id"]
    _comprueba(not pedidos_nuevos.empty and pedidos_nuevos.isin(nuevos.index).all(),
               "Conserva los pedidos con la categoría nueva y comprueba que se puedan transformar.")
    return (
        f"Separación estratificada de {len(train)} filas de train y {len(prueba)} de prueba. "
        "Ajuste guardado y aprendido solo con train. Producción se transforma con la categoría nueva."
    )


def evaluar(etapa=4):
    """Revisa desde la etapa 0 hasta la indicada y señala la primera pendiente."""
    try:
        historial = leer_historial()
        _comprueba(historial, "Haz una primera medición con medir.")
        print("Etapa 0 · Hay una medición registrada.")
        if etapa == 0:
            return True
        _comprueba(ULTIMA.is_file(), "Vuelve a medir para guardar la última tabla preparada.")
        info = joblib.load(ULTIMA)
        _comprueba(info["registro"]["fecha"] == historial[-1]["fecha"],
                   "Vuelve a medir para sincronizar el historial y la última preparación.")
        crudo, crudos_nuevos = cargar_datos()
    except FaltaEtapa as error:
        print(f"Completa primero la etapa 0. {error}")
        return False
    except Exception:
        print("Revisa los archivos de datos y vuelve a medir.")
        return False

    verificaciones = (_etapa_1, _etapa_2, _etapa_3, _etapa_4)
    for numero, comprobar in enumerate(verificaciones[:etapa], 1):
        try:
            resultado = comprobar(info, crudo, crudos_nuevos)
        except FaltaEtapa as error:
            aviso = f"Completa primero la etapa {numero}. " if numero < etapa else ""
            print(f"Etapa {numero} · {aviso}{error}")
            return False
        except Exception:
            print(f"Etapa {numero} · Revisa la preparación con tu agente y vuelve a medir.")
            return False
        print(f"Etapa {numero} · {resultado}")
    return True


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Comprueba las etapas de Nimbus.")
    argumentos.add_argument("etapa", type=int, nargs="?", default=4, choices=range(5))
    raise SystemExit(0 if evaluar(argumentos.parse_args().etapa) else 1)
