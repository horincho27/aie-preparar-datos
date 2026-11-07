"""Ejecutá python run_all.py desde la raíz: base preparada y tres etapas."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from preparar.listo.extraer import cargar_fuentes, unir
from preparar.listo.explorar import informe
from preparar.listo.duplicados import eliminar_duplicados
from preparar.listo.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from preparar.listo.validar import validar, aplicar_reglas
from preparar.listo.enriquecer import precio_unitario
from preparar.listo.pipeline import ajustar_y_transformar
from preparar.listo.cargar import guardar
from preparar.listo.estado import ejecutar_etapa, EtapaPendiente
from preparar.faltantes import agregar_indicador_faltante, comparar_tasa
from preparar.enriquecer import dias_desde_registro, quitar_filtracion
from preparar.pipeline import separar, construir_pipeline


def main():
    pedidos, clientes = cargar_fuentes()
    tabla, registro = unir(pedidos, clientes)
    print(f"Listo · Extraer: {registro['antes']} pedidos -> {registro['despues']} filas unidas")
    resumen = informe(tabla)
    print(f"Listo · Explorar: {resumen['filas']} filas, {resumen['duplicados_exactos']} duplicados exactos")
    tabla, eliminadas = eliminar_duplicados(tabla)
    print(f"Listo · Duplicados: {eliminadas} eliminados -> {len(tabla)} filas")
    tabla["price"] = convertir_precio(tabla["price"])
    tabla["order_date"] = convertir_fecha(tabla["order_date"])
    tabla["category"] = estandarizar_categoria(tabla["category"])
    print(f"Listo · Tipos: {len(tabla)} filas, {tabla['order_date'].isna().sum()} fechas ilegibles")
    tabla, rechazadas = validar(tabla)
    tabla, limitadas = aplicar_reglas(tabla)
    print(f"Listo · Validar: {rechazadas} rechazadas, {limitadas} descuentos limitados -> {len(tabla)} filas")
    tabla = ejecutar_etapa(1, agregar_indicador_faltante, tabla, "phone")
    tasas = ejecutar_etapa(1, comparar_tasa, tabla, "phone_missing")
    print(f"Etapa 1 · Faltantes: {len(tabla)} filas; sin teléfono {tasas[1]:.1%}, con teléfono {tasas[0]:.1%}")
    tabla = ejecutar_etapa(2, dias_desde_registro, tabla)
    tabla = precio_unitario(tabla)
    tabla = ejecutar_etapa(2, quitar_filtracion, tabla)
    print(f"Etapa 2 · Sin futuro: {len(tabla)} filas, características disponibles al recibir el pedido")
    train, test = ejecutar_etapa(3, separar, tabla)
    pipeline = ejecutar_etapa(3, construir_pipeline)
    train, test = ajustar_y_transformar(train, test, pipeline)
    print(f"Etapa 3 · Separar y preparar: {len(train)} entrenamiento, {len(test)} prueba")
    guardar(train, test, pipeline)
    print(f"Listo · Guardar: {len(train) + len(test)} filas en data/processed")


if __name__ == "__main__":
    try:
        main()
    except EtapaPendiente as error:
        print(error)
        sys.exit(1)
    except FileNotFoundError:
        print("Faltan datos locales. Revisá data/raw y volvé a ejecutar python run_all.py.")
        sys.exit(1)
