# Lo que ya está hecho

Lee este recorrido para ubicar tu trabajo. Estas funciones vienen resueltas y comentadas. Durante la práctica, completa las tres etapas indicadas.

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
18. `evaluar.py` entrena el modelo fijo y muestra el efecto de cada etapa completa.

**El precio vacío NO se rellena en esta parte.** Se conserva hasta la etapa 3: el imputador aprende la mediana únicamente de train. Un faltante no se convierte en cero ni se elimina por ser desconocido.

`cargar.preparar_base` agrupa los pasos iniciales; `cargar.preparar_crudos` añade las etapas 1 y 2 y el precio unitario, tanto para entrenamiento como para producción. La comparación de tasas usa etiquetas y solo se hace con pedidos históricos.

Para comparar en clase, `pipeline.version_mal(df)` usa las funciones que completas en la etapa 3 y ajusta con toda la tabla antes de separar. Así puedes ver qué ocurre cuando el ajuste incluye la prueba.

`estado.py` ayuda a indicar qué etapa falta. El evaluador usa los valores y el transformador de referencia de `listo/` en las otras dos etapas. Así, cada comparación cambia una sola cosa. Puedes ejecutar `python evaluar.py` después de cada etapa. El comando calcula el informe a partir de los datos del proyecto.

## Ejemplos de la salida

Los puntos suspensivos indican los valores que se calculan al completar la etapa.

```text
Etapa 1 · El dato que falta
Qué hiciste · Marcaste los pedidos sin teléfono y comparaste las tasas de devolución.
Tasas de devolución · Con teléfono … %, sin teléfono … %.
Antes · F1 en producción sin el indicador ….
Después · F1 en producción con el indicador ….
Qué significa · El indicador permite que el modelo use la diferencia entre los dos grupos.
```

```text
Etapa 2 · La columna que hace trampa
Qué hiciste · Calculaste los días desde el registro y quitaste el monto y el motivo de devolución.
Antes · Con los datos futuros, F1 en prueba … y en producción ….
Después · Sin los datos futuros, F1 en prueba … y en producción ….
Días desde el registro · Dos cálculos sobre … pedidos dieron ….
Qué significa · El reembolso adelanta la respuesta en la prueba, pero aún no existe cuando llega un pedido nuevo.
```

```text
Etapa 3 · Separar y preparar sin filtración
Qué hiciste · Separaste los pedidos y ajustaste la preparación solo con los de entrenamiento.
Si ajustaras con todo · … de … pedidos. Mediana aprendida …. F1 en prueba … y en producción ….
Tu ajuste · … de … pedidos. Mediana aprendida … frente a … en el total. F1 en prueba … y en producción ….
Devoluciones · Entrenamiento … %. Prueba … %.
Producción · … pedidos transformados sin volver a ajustar.
Diferencia de F1 (ajuste con todo menos ajuste con entrenamiento) · Prueba …, producción ….
Qué significa · En esta comparación, ajustar con todo …. Ese ajuste incluye los pedidos de prueba y compromete la evaluación.
```

Cuando las tres etapas están completas, aparece la tabla con las filas «Correcta», «Con datos del futuro» y «Siempre cero». La práctica termina al ver el antes y el después de cada etapa. Comparte en voz alta en clase la línea **«Mi F1 en producción: 0,XX»**.
