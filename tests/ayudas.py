"""Encadena funciones existentes; no resuelve las tareas del alumno."""
from preparar.listo.extraer import cargar_fuentes
from preparar.listo.cargar import preparar_base
from preparar.listo.enriquecer import precio_unitario
from preparar.faltantes import agregar_indicador_faltante
from preparar.enriquecer import dias_desde_registro, quitar_filtracion


def hasta(etapa):
    pedidos, clientes = cargar_fuentes()
    tabla, _ = preparar_base(pedidos, clientes)
    if etapa >= 1:
        tabla = agregar_indicador_faltante(tabla, "phone")
    if etapa >= 2:
        tabla = dias_desde_registro(tabla)
        tabla = precio_unitario(tabla)
        tabla = quitar_filtracion(tabla)
    return tabla
