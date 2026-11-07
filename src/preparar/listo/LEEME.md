# Lo que ya está hecho

Leé este recorrido para ubicar tu trabajo. Estas funciones vienen resueltas y comentadas; durante la práctica solo completás las tres etapas indicadas.

1. `extraer.cargar_fuentes`: lee los pedidos CSV y los clientes JSON locales.
2. `extraer.unir`: junta por cliente con left join y registra filas antes y después.
3. `explorar.informe`: cuenta ausencias, tipos, duplicados y tasa de devolución.
4. `duplicados.eliminar_duplicados`: quita solo filas idénticas; conserva compras con otro `order_id`.
5. `tipos.convertir_precio`: interpreta los formatos de texto como números.
6. `tipos.convertir_fecha`: admite los dos formatos y deja `NaT` en fechas ilegibles.
7. `tipos.estandarizar_categoria`: unifica mayúsculas y espacios.
8. `validar.validar`: rechaza valores imposibles y conserva los precios desconocidos.
9. `validar.aplicar_reglas`: limita descuentos entre 0 y 1 sin borrar esas filas.
10. **Tu etapa 1, `../faltantes.py`:** crea el indicador de teléfono ausente y compara las tasas.
11. **Tu etapa 2, `../enriquecer.py`:** calcula días desde el registro usando la fecha del pedido.
12. `enriquecer.precio_unitario`: divide precio por cantidad con protección contra cero.
13. **Tu etapa 2, `../enriquecer.py`:** elimina las dos columnas que revelan el futuro.
14. **Tu etapa 3, `../pipeline.py`:** separa train/test y construye el transformador sin ajustar.
15. `pipeline.ajustar_y_transformar`: ajusta solo con train y transforma train/test, conservando nombres y etiqueta.
16. `cargar.guardar`: escribe CSV, joblib y esquema; `order_id` queda como índice, nunca como predictor.
17. `cargar.aplicar_a_nuevos`: reutiliza la base y tus etapas 1 y 2; luego transforma con el joblib sin reajustar.
18. `evaluar.py`: entrena el modelo fijo y compara prueba con producción.

**El precio vacío NO se rellena en esta parte.** Se conserva hasta la etapa 3: el imputador aprende la mediana únicamente de train. Un faltante no se convierte en cero ni se elimina por ser desconocido.

`cargar.preparar_base` agrupa los pasos iniciales; `cargar.preparar_crudos` añade las etapas 1 y 2 y el precio unitario, tanto para entrenamiento como para producción. La comparación de tasas usa etiquetas y solo se hace con pedidos históricos.

Para comparar en clase, `pipeline.version_mal(df)` viene resuelta. Usa las funciones que completás en la etapa 3, pero ajusta con toda la tabla antes de separar: es el error que queremos reconocer. No se usa en `run_all.py`.

`estado.py` y `recorrido.py` solo ayudan a mostrar cuál de las tres etapas falta, sin errores técnicos en pantalla.
