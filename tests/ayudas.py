"""Solo encadenan las funciones del alumno: no contienen limpieza resuelta."""
from preparar.extraer import cargar_fuentes, unir
from preparar.duplicados import eliminar_duplicados
from preparar.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from preparar.validar import validar, aplicar_reglas
from preparar.faltantes import agregar_indicador_faltante
from preparar.enriquecer import dias_desde_registro, precio_unitario, quitar_filtracion

def hasta(etapa):
    pedidos, clientes = cargar_fuentes()
    tabla, _ = unir(pedidos, clientes)
    if etapa >= 3:
        tabla, _ = eliminar_duplicados(tabla)
    if etapa >= 4:
        tabla["price"] = convertir_precio(tabla["price"])
        tabla["order_date"] = convertir_fecha(tabla["order_date"])
        tabla["category"] = estandarizar_categoria(tabla["category"])
    if etapa >= 5:
        tabla, _ = validar(tabla)
        tabla, _ = aplicar_reglas(tabla)
    if etapa >= 6:
        tabla = agregar_indicador_faltante(tabla, "phone")
    if etapa >= 7:
        tabla = dias_desde_registro(tabla)
        tabla = precio_unitario(tabla)
        tabla = quitar_filtracion(tabla)
    return tabla
