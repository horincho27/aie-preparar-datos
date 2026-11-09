"""Balanza de Nimbus. Llama a medir con tu función de preparación."""

import base64
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import NotFittedError
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted


RAIZ = Path(__file__).resolve().parent
HISTORIAL = RAIZ / "mediciones.csv"
PROCESADOS = RAIZ / "data/processed"
ULTIMA = PROCESADOS / "ultima_medicion.joblib"
PREPARACION = PROCESADOS / "preparacion.joblib"


class ProblemaMedicion(ValueError):
    """Un problema que el alumno puede revisar con su agente."""


def _configurar_salida_utf8():
    # La consola puede usar otra codificación. El notebook ya admite texto Unicode.
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def cargar_datos():
    """Devuelve pedidos históricos y nuevos unidos con los datos de clientes."""
    clientes = pd.read_json(RAIZ / "data/raw/customers.json", convert_dates=False)
    historico = pd.read_csv(RAIZ / "data/raw/orders.csv", dtype={"price": "string"})
    nuevos = pd.read_csv(RAIZ / "data/new/orders_new.csv", dtype={"price": "string"})
    # Cada cliente aporta sus datos a todos sus pedidos. Conservamos cada pedido.
    return tuple(
        pedidos.merge(clientes, on="customer_id", how="left", validate="many_to_one")
        for pedidos in (historico, nuevos)
    )


def campos_exclusivos(historico, nuevos):
    """Devuelve los campos que no forman parte del esquema de un pedido nuevo."""
    return historico.columns.difference([*nuevos.columns, "returned"], sort=False).tolist()


def _alias_exclusivos(historico, nuevos):
    return {
        campo: f"campo exclusivo del histórico {i}"
        for i, campo in enumerate(campos_exclusivos(historico, nuevos), 1)
    }


def _nombre_visible(columna, reservadas):
    # El diagnóstico localiza los problemas sin anticipar la respuesta de la etapa 2.
    return reservadas.get(columna, str(columna))


def _diagnostico(tabla, nombre, reservadas):
    textos = tabla.select_dtypes(include=["object", "string", "category"]).columns
    vacios = tabla.isna().sum()
    nombres = ", ".join(_nombre_visible(c, reservadas) for c in textos)
    cantidades = ", ".join(
        f"{_nombre_visible(c, reservadas)} ({n})" for c, n in vacios.items() if n
    )
    print(f"{nombre} · {len(tabla)} filas.")
    print(f"  Columnas de texto · {nombres or 'ninguna'}.")
    print(f"  Vacíos por columna · {cantidades or 'ninguno'}.")


def _revisar_tabla(tabla, cruda, nombre):
    if not isinstance(tabla, pd.DataFrame) or tabla.empty:
        raise ProblemaMedicion(f"Devuelve una tabla de pandas con filas para {nombre}.")
    if not tabla.columns.is_unique:
        raise ProblemaMedicion(f"Usa nombres de columnas únicos en {nombre}.")
    if "order_id" not in tabla or not tabla["order_id"].isin(cruda["order_id"]).all():
        raise ProblemaMedicion(f"Conserva los identificadores order_id originales en {nombre}.")


def separar_pedidos(tabla):
    """Separa identificadores 80/20 y mantiene juntas las copias de cada pedido."""
    ids = tabla[["order_id", "returned"]].drop_duplicates("order_id")
    # La etiqueta mantiene proporciones parecidas en los dos grupos.
    # Aquí elegimos identificadores. La tabla del alumno conserva todas sus filas.
    train, prueba = train_test_split(
        ids["order_id"], test_size=0.2, stratify=ids["returned"], random_state=42
    )
    return train.tolist(), prueba.tolist()


def _entradas(historico, nuevos, ids_train, ids_prueba):
    historico = historico.set_index("order_id")
    train = historico.loc[ids_train]
    prueba = historico.loc[ids_prueba]
    # El identificador sirve para alinear filas. La etiqueta es lo que se predice.
    return (
        train.drop(columns="returned"), prueba.drop(columns="returned"),
        nuevos.set_index("order_id"), train["returned"], prueba["returned"],
    )


def _revisar_matriz(matriz, nombre):
    valores = matriz.data if sparse.issparse(matriz) else np.asarray(matriz)
    if (
        len(matriz.shape) != 2 or matriz.shape[1] == 0
        or valores.dtype.kind not in "biuf" or not np.isfinite(valores).all()
    ):
        raise ProblemaMedicion(
            f"Revisa {nombre}. El modelo necesita columnas numéricas sin vacíos ni infinitos."
        )


def _seleccionar_columnas(columnas, seleccion):
    """Lee los nombres de origen de un selector del transformador."""
    if isinstance(seleccion, str):
        return [seleccion]
    if isinstance(seleccion, (int, np.integer)):
        return [columnas[seleccion]]
    if isinstance(seleccion, slice):
        if isinstance(seleccion.start, str) or isinstance(seleccion.stop, str):
            seleccion = columnas.slice_indexer(seleccion.start, seleccion.stop, seleccion.step)
        return columnas[seleccion].tolist()
    seleccion = list(seleccion)
    if not seleccion or isinstance(seleccion[0], str):
        return seleccion
    return columnas[seleccion].tolist()


def _entradas_del_ajuste(ajuste, tabla):
    if isinstance(ajuste, ColumnTransformer):
        entradas = []
        rellenadas = set()
        for nombre, paso, seleccion in ajuste.transformers_:
            salida = ajuste.output_indices_[nombre]
            if salida.start == salida.stop:
                continue
            columnas = _seleccionar_columnas(tabla.columns, seleccion)
            usadas, llenas = _entradas_del_ajuste(paso, tabla[columnas])
            entradas.extend(usadas)
            rellenadas.update(llenas)
        return list(dict.fromkeys(entradas)), rellenadas
    if isinstance(ajuste, Pipeline):
        # El primer paso recibe las columnas originales de esta rama.
        primero = next(
            (paso for paso in ajuste.named_steps.values() if paso not in (None, "passthrough")),
            None,
        )
        return _entradas_del_ajuste(primero, tabla)
    rellenadas = set(tabla.columns[tabla.isna().any()]) if isinstance(ajuste, SimpleImputer) else set()
    return tabla.columns.tolist(), rellenadas


def _numericas_completas(tabla):
    numericas = tabla.select_dtypes(include="number")
    return [
        c for c in numericas if np.isfinite(numericas[c].to_numpy(dtype=float, na_value=np.nan)).all()
    ]


def _preparar_entradas(train, prueba, nuevos, transformador):
    if transformador is None:
        # Elegimos las entradas del modelo solo con entrenamiento. No alteramos la tabla.
        completas = _numericas_completas(train)
        if not completas:
            raise ProblemaMedicion("Deja al menos una columna numérica completa para medir.")
        return (train[completas], prueba[completas], nuevos[completas]), None, None, completas, set()

    try:
        check_is_fitted(transformador)
    except NotFittedError:
        pass
    else:
        raise ProblemaMedicion("Pasa un transformador sin ajustar. La balanza lo ajusta con train.")
    # Ajustar aprende valores. Transformar solo usa lo aprendido.
    ajuste = clone(transformador)
    ajuste.fit(train)
    estado = joblib.hash(ajuste)
    matrices = tuple(ajuste.transform(tabla) for tabla in (train, prueba, nuevos))
    if joblib.hash(ajuste) != estado:
        raise ProblemaMedicion("Transformar cambió el ajuste. Revisa que transform solo aplique lo aprendido.")
    evidencia = {"ids": train.index.unique().tolist(), "estado": estado}
    entradas, rellenadas = _entradas_del_ajuste(ajuste, train)
    print(f"Transformador · Ajustado con {len(train)} filas de entrenamiento.")
    return matrices, ajuste, evidencia, entradas, rellenadas


def _respuestas(crudos_nuevos, ids):
    # Las etiquetas de producción se leen después de entrenar y nunca llegan a preparar.
    codificadas = (RAIZ / "data/new/.respuestas").read_bytes()
    reales = pd.Series(json.loads(base64.b64decode(codificadas)), index=crudos_nuevos["order_id"])
    return reales.loc[ids]


def _puntajes(reales, predichas):
    return {
        "f1": f1_score(reales, predichas, zero_division=0),
        "detectadas": int(((reales == 1) & (predichas == 1)).sum()),
        "devoluciones": int(reales.sum()),
        "exactitud": accuracy_score(reales, predichas),
    }


def leer_historial():
    if not HISTORIAL.exists():
        return []
    with HISTORIAL.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _medicion_anterior(anterior):
    if anterior is None or not ULTIMA.is_file():
        return {}
    try:
        info = joblib.load(ULTIMA)
        if info["registro"]["fecha"] == anterior["fecha"]:
            # Las mediciones anteriores al cambio no guardaban sus entradas por separado.
            if "entradas_modelo" not in info:
                train = _entradas(
                    info["historico"], info["nuevos"], info["ids_train"], info["ids_prueba"]
                )[0]
                if info["ajuste"] is None:
                    info["entradas_modelo"] = _numericas_completas(train)
                elif PREPARACION.is_file():
                    ajuste = joblib.load(PREPARACION)
                    if joblib.hash(ajuste) == info["ajuste"]["estado"]:
                        info["entradas_modelo"] = _entradas_del_ajuste(ajuste, train)[0]
            return info
    except Exception:
        # El historial de puntajes sigue disponible aunque falte el detalle de entradas.
        pass
    return {}


def _mostrar_entradas(entradas, rellenadas, anteriores, reservadas, tiene_ajuste):
    usadas = ", ".join(_nombre_visible(c, reservadas) for c in entradas)
    print(f"Entradas del modelo · {usadas}.")
    nuevas = []
    if anteriores is not None:
        nuevas = [c for c in entradas if c not in anteriores]
        retiradas = [c for c in anteriores if c not in entradas]
        if nuevas:
            nombres = ", ".join(
                _nombre_visible(c, reservadas) + (" (con vacíos rellenados)" if c in rellenadas else "")
                for c in nuevas
            )
            print(f"Nuevas entradas: {nombres}.")
        if retiradas:
            nombres = ", ".join(_nombre_visible(c, reservadas) for c in retiradas)
            print(f"Entradas retiradas · {nombres}.")
    if tiene_ajuste:
        cambio = (
            "El transformador permite usar las entradas nuevas."
            if nuevas else "El transformador prepara las entradas del modelo."
        )
        print(f"Qué cambió · {cambio} El ajuste se hizo solo con train para mantener la prueba separada.")


def _resumen(fila, conjunto):
    if fila is None:
        return "sin medición"
    f1 = f"{float(fila[f'f1_{conjunto}']):.3f}".replace(".", ",")
    exactitud = f"{100 * float(fila[f'exactitud_{conjunto}']):.2f}".replace(".", ",")
    detectadas = fila[f"detectadas_{conjunto}"]
    devoluciones = fila[f"devoluciones_{conjunto}"]
    return f"F1 {f1}, detectadas {detectadas} de {devoluciones}, exactitud {exactitud} %"


def medir(preparar, etapa=0, transformador=None):
    """Mide la tabla devuelta por preparar y registra una medición si puede entrenar."""
    _configurar_salida_utf8()
    reservadas = {}
    try:
        if etapa not in range(5):
            raise ProblemaMedicion("Indica una etapa entre 0 y 4.")
        crudo, crudos_nuevos = cargar_datos()
        reservadas = _alias_exclusivos(crudo, crudos_nuevos)
        # Usamos la misma función en las dos tablas y cada llamada recibe su propia copia.
        historico = preparar(crudo.copy())
        nuevos = preparar(crudos_nuevos.copy())
        _revisar_tabla(historico, crudo, "el histórico")
        _revisar_tabla(nuevos, crudos_nuevos, "producción")
        _diagnostico(historico, "Histórico preparado", reservadas)
        _diagnostico(nuevos, "Producción preparada", reservadas)
        if "returned" not in historico:
            raise ProblemaMedicion("Falta returned. Conserva la etiqueta en la tabla histórica.")
        if "returned" in nuevos:
            raise ProblemaMedicion("Conserva returned solo en la tabla histórica.")
        etiquetas = crudo.drop_duplicates("order_id").set_index("order_id")["returned"]
        if not historico["returned"].eq(historico["order_id"].map(etiquetas)).all():
            raise ProblemaMedicion("Conserva los valores originales de returned.")
        solo_historico = historico.columns.difference([*nuevos.columns, "returned"], sort=False)
        solo_nuevos = nuevos.columns.difference(historico.columns, sort=False)
        if len(solo_historico) or len(solo_nuevos):
            extra_h = ", ".join(_nombre_visible(c, reservadas) for c in solo_historico) or "ninguna"
            extra_n = ", ".join(_nombre_visible(c, reservadas) for c in solo_nuevos) or "ninguna"
            print(f"Solo en histórico · {extra_h}. Solo en producción · {extra_n}.")
            raise ProblemaMedicion(
                "Haz que preparar devuelva las mismas columnas para las dos tablas, aparte de returned."
            )

        ids_train, ids_prueba = separar_pedidos(historico)
        train, prueba, entrada_nuevos, y_train, y_prueba = _entradas(
            historico, nuevos, ids_train, ids_prueba
        )
        matrices, ajuste, evidencia, entradas, rellenadas = _preparar_entradas(
            train, prueba, entrada_nuevos, transformador
        )
        for matriz, nombre in zip(matrices, ("entrenamiento", "prueba", "producción")):
            _revisar_matriz(matriz, nombre)
        historial = leer_historial()
        anterior = historial[-1] if historial else None
        info_anterior = _medicion_anterior(anterior)
        _mostrar_entradas(
            entradas, rellenadas, info_anterior.get("entradas_modelo"), reservadas, ajuste is not None
        )
        # La clase menos frecuente recibe más peso según sus ejemplos en entrenamiento.
        modelo = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
        modelo.fit(matrices[0], y_train)
        y_nuevos = _respuestas(crudos_nuevos, entrada_nuevos.index)
        fila = {"etapa": etapa, "fecha": datetime.now(timezone.utc).isoformat()}
        for conjunto, reales, matriz in (
            ("prueba", y_prueba, matrices[1]), ("produccion", y_nuevos, matrices[2])
        ):
            for nombre, valor in _puntajes(reales, modelo.predict(matriz)).items():
                fila[f"{nombre}_{conjunto}"] = valor

        repetible = sin_futuro = None
        if etapa >= 2:
            # El verificador mira el resultado al repetir la llamada y al ocultar el futuro.
            repetible = historico.equals(preparar(crudo.copy()))
            sin_informacion = crudo.copy()
            for columna in reservadas:
                sin_informacion[columna] = pd.NA
            sin_futuro = historico.equals(preparar(sin_informacion))

        PROCESADOS.mkdir(parents=True, exist_ok=True)
        if ajuste is not None:
            joblib.dump(ajuste, PREPARACION)
        joblib.dump({
            "registro": fila, "historico": historico, "nuevos": nuevos,
            "ids_train": ids_train, "ids_prueba": ids_prueba,
            "repetible": repetible, "sin_futuro": sin_futuro, "ajuste": evidencia,
            "entradas_modelo": entradas, "ponderacion": "balanced",
        }, ULTIMA)
        with HISTORIAL.open("a", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=list(fila))
            if not historial:
                escritor.writeheader()
            escritor.writerow(fila)
    except ProblemaMedicion as error:
        print(f"Aún no se puede medir. {error}")
        return None
    except Exception as error:
        # El alumno recibe un mensaje breve incluso si su función levanta una excepción.
        detalle = str(error).splitlines()[0] if str(error) else type(error).__name__
        for campo, alias in reservadas.items():
            detalle = detalle.replace(campo, alias)
        print(f"Aún no se puede medir. Revisa preparar y el diagnóstico con tu agente. {detalle}")
        return None

    print(f"Medición guardada · Etapa {etapa}.")
    if info_anterior and info_anterior.get("ponderacion") != "balanced":
        print("La medición anterior corresponde a la versión del modelo sin ponderación de clases.")
    for conjunto, nombre in (("prueba", "Prueba"), ("produccion", "Producción")):
        print(f"{nombre} · Antes {_resumen(anterior, conjunto)}. Ahora {_resumen(fila, conjunto)}.")
    if (
        etapa == 1 and anterior and set(entradas).intersection(reservadas)
        and fila["f1_prueba"] > fila["f1_produccion"]
        and all(fila[c] == float(anterior[c]) for c in ("f1_prueba", "f1_produccion"))
    ):
        print("El F1 todavía no cambia. El modelo sigue usando información que le adelanta la respuesta.")
    return fila
