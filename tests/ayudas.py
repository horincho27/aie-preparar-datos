"""Encadena funciones existentes; no resuelve las tareas del alumno."""
from preparar.listo.extraer import cargar_fuentes
from preparar.listo.cargar import preparar_base
from preparar.listo.enriquecer import precio_unitario
from preparar.faltantes import agregar_indicador_faltante
from preparar.enriquecer import dias_desde_registro, quitar_filtracion


def _ejecutar_etapa_previa(numero, funcion, *argumentos):
    try:
        return funcion(*argumentos)
    except NotImplementedError as error:
        raise NotImplementedError(f"Completa primero la etapa {numero}.") from error


def hasta(etapa):
    pedidos, clientes = cargar_fuentes()
    tabla, _ = preparar_base(pedidos, clientes)
    if etapa >= 1:
        tabla = _ejecutar_etapa_previa(1, agregar_indicador_faltante, tabla, "phone")
    if etapa >= 2:
        tabla = _ejecutar_etapa_previa(2, dias_desde_registro, tabla)
        tabla = precio_unitario(tabla)
        tabla = _ejecutar_etapa_previa(2, quitar_filtracion, tabla)
    return tabla
