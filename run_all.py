"""Ejecutá python run_all.py desde la raíz del proyecto."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from preparar.extraer import cargar_fuentes, unir
from preparar.explorar import informe
from preparar.duplicados import eliminar_duplicados
from preparar.tipos import convertir_precio, convertir_fecha, estandarizar_categoria
from preparar.validar import validar, aplicar_reglas
from preparar.faltantes import agregar_indicador_faltante, comparar_tasa
from preparar.enriquecer import dias_desde_registro, precio_unitario, quitar_filtracion
from preparar.pipeline import separar, construir_pipeline, ajustar_y_transformar
from preparar.cargar import guardar

def main():
    pedidos, clientes = cargar_fuentes()
    tabla, registro = unir(pedidos, clientes)
    print(f"1 · Extraer: {registro['antes']} pedidos -> {registro['despues']} filas unidas")
    resumen = informe(tabla)
    print(f"2 · Explorar: {resumen['filas']} filas, {resumen['duplicados_exactos']} duplicados exactos")
    tabla, eliminadas = eliminar_duplicados(tabla)
    print(f"3 · Duplicados: {eliminadas} eliminados -> {len(tabla)} filas")
    tabla["price"] = convertir_precio(tabla["price"])
    tabla["order_date"] = convertir_fecha(tabla["order_date"])
    tabla["category"] = estandarizar_categoria(tabla["category"])
    print(f"4 · Tipos: {len(tabla)} filas, {tabla['order_date'].isna().sum()} fechas ilegibles")
    tabla, rechazadas = validar(tabla)
    tabla, limitadas = aplicar_reglas(tabla)
    print(f"5 · Validar: {rechazadas} rechazadas, {limitadas} descuentos limitados -> {len(tabla)} filas")
    tabla = agregar_indicador_faltante(tabla, "phone")
    tasas = comparar_tasa(tabla, "phone_missing")
    print(f"6 · Faltantes: {len(tabla)} filas; sin teléfono {tasas[1]:.1%}, con teléfono {tasas[0]:.1%}")
    tabla = dias_desde_registro(tabla)
    tabla = precio_unitario(tabla)
    tabla = quitar_filtracion(tabla)
    print(f"7 · Enriquecer: {len(tabla)} filas, características disponibles al recibir el pedido")
    train, test = separar(tabla)
    pipeline = construir_pipeline()
    train, test = ajustar_y_transformar(train, test, pipeline)
    print(f"8 · Separar y preparar: {len(train)} entrenamiento, {len(test)} prueba")
    guardar(train, test, pipeline)
    print(f"9 · Cargar: guardadas {len(train) + len(test)} filas en data/processed")

if __name__ == "__main__":
    try:
        main()
    except NotImplementedError:
        print("Todavía falta resolver una etapa. Completá las funciones en orden y revisá sus tests.")
        sys.exit(1)
