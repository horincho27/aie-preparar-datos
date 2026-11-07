# Comprueba en orden las funciones pendientes antes de evaluar archivos guardados.
# Corresponde al recorrido de la práctica: primero ausencia, luego futuro y separación.
from preparar.faltantes import agregar_indicador_faltante, comparar_tasa
from preparar.enriquecer import dias_desde_registro, quitar_filtracion
from preparar.pipeline import separar, construir_pipeline
from preparar.listo.extraer import cargar_fuentes
from preparar.listo.cargar import preparar_base
from preparar.listo.enriquecer import precio_unitario
from preparar.listo.estado import ejecutar_etapa


def comprobar_etapas():
    """Comprueba las tres etapas sin guardar ni ajustar ningún transformador."""
    pedidos, clientes = cargar_fuentes()
    tabla, _ = preparar_base(pedidos, clientes)
    tabla = ejecutar_etapa(1, agregar_indicador_faltante, tabla, "phone")
    ejecutar_etapa(1, comparar_tasa, tabla, "phone_missing")
    tabla = ejecutar_etapa(2, dias_desde_registro, tabla)
    tabla = precio_unitario(tabla)
    tabla = ejecutar_etapa(2, quitar_filtracion, tabla)
    ejecutar_etapa(3, separar, tabla)
    ejecutar_etapa(3, construir_pipeline)
