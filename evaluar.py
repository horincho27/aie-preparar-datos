"""Comprueba lo que quedó preparado en la última medición."""

import argparse
from datetime import datetime
from functools import partial
from math import ceil

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone

from medir import (
    PREPARACION, ULTIMA, _alias_exclusivos, _configurar_salida_utf8,
    _diagnostico, _entradas, _revisar_matriz, cargar_datos, campos_exclusivos,
    leer_historial,
)


class FaltaEtapa(ValueError):
    """Una condición de la etapa que todavía no se cumple."""


def _comprueba(condicion, mensaje):
    if not condicion:
        raise FaltaEtapa(mensaje)


def _fecha_original(texto):
    try:
        formato = "%d/%m/%Y" if "/" in texto else "%Y-%m-%d"
        return datetime.strptime(texto, formato)
    except (TypeError, ValueError):
        return pd.NaT


def _valor_visible(valor):
    return "vacío" if pd.isna(valor) else str(valor)


def _comprobar_valores(crudos, obtenidos, distintos, mensaje):
    fallos = crudos.index[distintos]
    if len(fallos):
        ejemplos = "\n".join(
            f"  {pedido} · {_valor_visible(crudos.at[pedido])} -> "
            f"{_valor_visible(obtenidos.get(pedido, 'pedido eliminado'))}"
            for pedido in fallos[:2]
        )
        raise FaltaEtapa(f"{mensaje}\n{ejemplos}")


def _comprobar_filas(tabla, crudo, precios, fechas, nombre):
    presentes = crudo.index.isin(tabla.index)
    imposibles = precios.le(0)
    ilegibles = fechas.isna()
    precios_vacios = tabla["price"].reindex(crudo.index).isna()
    _comprobar_valores(
        crudo["price"], tabla["price"], presentes & imposibles & precios_vacios,
        f"Convertiste precios imposibles en vacíos en {nombre}. Quita esos pedidos. "
        "Si el precio se rellena más adelante, el vacío esconde el error.",
    )
    _comprobar_valores(
        crudo["price"], tabla["price"], presentes & imposibles,
        f"Quita los pedidos con precio original menor o igual a 0 en {nombre}.",
    )
    _comprobar_valores(
        crudo["order_date"], tabla["order_date"], presentes & ilegibles,
        f"Conservaste pedidos con fechas ilegibles en {nombre}. "
        "Quita esos pedidos aunque hayas dejado la fecha vacía.",
    )
    faltan = ~presentes & ~imposibles & ~ilegibles
    fechas_alternas = crudo["order_date"].str.contains("/", regex=False, na=False)
    _comprobar_valores(
        crudo["order_date"], tabla["order_date"], faltan & fechas_alternas,
        f"Quitaste pedidos con fechas válidas en formato dd/mm/aaaa en {nombre}. "
        "Convierte los dos formatos de fecha antes de quitar las ilegibles.",
    )
    _comprobar_valores(
        crudo["discount"], tabla["discount"], faltan & ~crudo["discount"].between(0, 1),
        f"Quitaste pedidos por su descuento en {nombre}. "
        "Conserva los pedidos y limita el descuento al borde de 0 a 1.",
    )
    _comprobar_valores(
        crudo.index.to_series(), tabla.index.to_series(), faltan,
        f"Quitaste pedidos válidos en {nombre}. Conserva las compras con otro identificador.",
    )


def _numeros_distintos(esperados, obtenidos):
    # Acepta pequeñas diferencias de representación, por debajo de un centavo.
    return ~np.isclose(esperados.astype(float), obtenidos.astype(float), rtol=1e-7, atol=1e-8, equal_nan=True)


def _limpieza(tabla, original, nombre):
    columnas = {"order_id", "price", "order_date", "category", "quantity", "discount"}
    _comprueba(columnas.issubset(tabla.columns), f"Conserva las columnas de limpieza en {nombre}.")
    _comprueba(tabla["order_id"].is_unique,
               f"Revisa los duplicados en {nombre}. Conserva las compras con otro identificador.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["price"]), f"Convierte price a número en {nombre}.")
    _comprueba(pd.api.types.is_datetime64_any_dtype(tabla["order_date"]),
               f"Convierte order_date a fecha en {nombre}.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["discount"]), f"Conserva discount como número en {nombre}.")
    _comprueba(pd.api.types.is_numeric_dtype(tabla["quantity"]), f"Conserva quantity como número en {nombre}.")

    crudo = original.drop_duplicates().set_index("order_id")
    tabla = tabla.set_index("order_id")
    precios = crudo["price"].map(lambda precio: np.nan if pd.isna(precio) else float(precio.replace(",", ".")))
    fechas = crudo["order_date"].map(_fecha_original)
    _comprobar_filas(tabla, crudo, precios, fechas, nombre)

    # Comparamos los pedidos por su identificador, aunque el alumno cambie el orden de las filas.
    crudo = crudo.loc[tabla.index]
    precios = precios.loc[tabla.index]
    fechas = fechas.loc[tabla.index]
    descuentos = crudo["discount"].clip(0, 1)
    descuentos_fuera = ~tabla["discount"].between(0, 1).fillna(False)
    categorias = crudo["category"].str.strip().str.lower()
    _comprobar_valores(
        crudo["price"], tabla["price"], precios.isna() & tabla["price"].notna(),
        f"Rellenaste precios que ya estaban vacíos en {nombre}. Consérvalos vacíos hasta la etapa 4.",
    )
    _comprobar_valores(
        crudo["price"], tabla["price"], _numeros_distintos(precios, tabla["price"]),
        f"Cambiaste el importe de price al convertirlo en {nombre}. Revisa el separador decimal de cada formato.",
    )
    _comprobar_valores(
        crudo["order_date"], tabla["order_date"], ~tabla["order_date"].eq(fechas),
        f"Cambiaste o perdiste una fecha válida en {nombre}. Revisa los dos formatos de order_date.",
    )
    _comprobar_valores(
        crudo["discount"], tabla["discount"],
        descuentos_fuera | _numeros_distintos(descuentos, tabla["discount"]),
        f"Revisa discount en {nombre}. Limita al borde los descuentos fuera de 0 a 1 "
        "y conserva el valor de los demás. Evita convertirlos en vacíos.",
    )
    _comprobar_valores(
        crudo["category"], tabla["category"], ~tabla["category"].eq(categorias).fillna(False),
        f"Unifica category en {nombre} con minúsculas y sin espacios en los bordes. Conserva su significado.",
    )
    _comprobar_valores(
        crudo["quantity"], tabla["quantity"], ~tabla["quantity"].eq(crudo["quantity"]).fillna(False),
        f"Conserva las cantidades originales en {nombre}.",
    )


def _por_pedido(crudo, columna, tabla):
    valores = crudo.drop_duplicates("order_id").set_index("order_id")[columna]
    return tabla["order_id"].map(valores)


def _etapa_1(info, crudo, crudos_nuevos, conservar_columnas):
    historico, nuevos = info["historico"], info["nuevos"]
    if conservar_columnas:
        exclusivas = campos_exclusivos(crudo, crudos_nuevos)
        _comprueba(set(exclusivas).issubset(historico.columns),
                   "Quitaste columnas que corresponden a la etapa 2.")
        _comprueba(set(crudo.columns).issubset(historico.columns)
                   and set(crudos_nuevos.columns).issubset(nuevos.columns),
                   "Conserva las columnas originales en la etapa 1.")
    _limpieza(historico, crudo, "el histórico")
    _limpieza(nuevos, crudos_nuevos, "producción")
    salieron = len(crudo) - len(info["historico"])
    salieron_nuevos = len(crudos_nuevos) - len(info["nuevos"])
    return f"Limpieza correcta. Salieron {salieron} filas del histórico y {salieron_nuevos} de producción."


def _etapa_2(info, crudo, crudos_nuevos):
    exclusivas = campos_exclusivos(crudo, crudos_nuevos)
    for tabla, original in ((info["historico"], crudo), (info["nuevos"], crudos_nuevos)):
        _comprueba("dias_desde_registro" in tabla, "Crea dias_desde_registro en las dos tablas.")
        registro = pd.to_datetime(_por_pedido(original, "signup_date", tabla), format="%Y-%m-%d")
        esperados = (tabla["order_date"] - registro).dt.days
        _comprueba(tabla["dias_desde_registro"].eq(esperados).all(),
                   "Calcula los días entre el registro y la fecha del pedido.")
        _comprueba(set(exclusivas).isdisjoint(tabla.columns),
                   "Revisa qué campos solo existen después de la devolución.")
    _comprueba(info["repetible"] is not None, "Vuelve a medir con etapa=2 para comprobar el resultado.")
    _comprueba(info["repetible"], "Prepara dos veces los mismos pedidos y obtén el mismo resultado.")
    _comprueba(info["sin_futuro"], "Evita que la preparación dependa de información posterior al pedido.")
    return "Días reproducibles y preparación sin datos del futuro."


def _etapa_3(info, crudo, crudos_nuevos):
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
    _configurar_salida_utf8()
    try:
        if etapa == 0:
            crudo, crudos_nuevos = cargar_datos()
            reservadas = _alias_exclusivos(crudo, crudos_nuevos)
            _diagnostico(crudo, "Histórico crudo", reservadas)
            _diagnostico(crudos_nuevos, "Producción cruda", reservadas)
        historial = leer_historial()
        _comprueba(any(fila["etapa"] == "0" for fila in historial),
                   "Guarda una primera medición con medir y etapa=0.")
        print("Etapa 0 · Hay una medición registrada con etapa=0.")
        if etapa == 0:
            return True
        _comprueba(ULTIMA.is_file(), "Vuelve a medir para guardar la última tabla preparada.")
        info = joblib.load(ULTIMA)
        _comprueba(info["registro"]["fecha"] == historial[-1]["fecha"],
                   "Vuelve a medir para sincronizar el historial y la última preparación.")
        # Al revisar etapas posteriores, sus tablas ya deben excluir los campos del futuro.
        conservar_columnas = etapa == 1 or int(info["registro"]["etapa"]) <= 1
        crudo, crudos_nuevos = cargar_datos()
    except FaltaEtapa as error:
        print(f"Completa primero la etapa 0. {error}")
        return False
    except Exception:
        print("Revisa los archivos de datos y vuelve a medir.")
        return False

    limpieza = partial(_etapa_1, conservar_columnas=conservar_columnas)
    verificaciones = (limpieza, _etapa_2, _etapa_3, _etapa_4)
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
