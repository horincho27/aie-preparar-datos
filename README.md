# Preparar datos · Tienda Nimbus

Proyecto para resolver en vivo, una etapa por vez. Nimbus es una tienda ficticia de ropa, electrónica, hogar y libros. Más adelante queremos predecir si un pedido se devolverá: `returned=1` significa que se devolvió y `returned=0` que no. Hoy preparamos los datos; todavía no elegimos modelos.

Todos los datos son inventados. No hace falta conectarse a una API ni descargar datasets. Hay 2.040 filas de pedidos históricos, 400 clientes y 200 pedidos nuevos. Los pedidos se relacionan con los clientes por `customer_id`. `price` es el importe del pedido antes del descuento, `discount` es una proporción y `quantity` es la cantidad de unidades. `category` representa una familia de productos; este caso no tiene `product_id`.

Trabajá en `src/preparar/`. Cada función indica qué recibe, qué devuelve y una pista. Al principio los tests de estructura pasan y los de las etapas fallan: son la lista de trabajo. No edites los tests ni el modelo fijo de `evaluar.py` para mejorar un puntaje. Anotá tus decisiones en `NOTAS.md`.

## Etapa 0 · Preparar el entorno

**Qué hacer:** abrí el repositorio con **Code → Codespaces → Create codespace**. Se usa Python 3.12 y se instalan las versiones de `requirements.txt`. En una terminal:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

Para trabajar localmente: `python -m venv .venv`, activá el entorno (`source .venv/bin/activate` en Linux/macOS o `.venv\Scripts\Activate.ps1` en PowerShell) e instalá los requisitos. Las pruebas son locales, sin internet después de instalar, y deben terminar en menos de 30 segundos.

**Por qué:** todos necesitamos las mismas versiones.

**Para qué:** comparar resultados reproducibles.

**Cómo verificar:** `pytest tests/test_estructura.py`. El resto falla hasta implementar sus etapas.

## Etapa 1 · Extraer

**Qué hacer:** resolvé `cargar_fuentes()` en `extraer.py` para leer `data/raw/orders.csv` y `customers.json`. `unir(orders, customers)` devuelve `(tabla, registro)` con un left join por `customer_id` y `registro` con `antes` y `despues`. Las fechas se convierten en la etapa 4.

**Por qué:** teléfono, registro y newsletter vienen de otra fuente.

**Para qué:** tener una tabla sin perder pedidos ni multiplicarlos por clientes repetidos.

**Cómo verificar:** `pytest tests/test_etapa_01_extraer.py`.

## Etapa 2 · Explorar

**Qué hacer:** `informe(df)` devuelve `filas`, `nulos` por columna, `duplicados_exactos`, `tipos` como textos y `tasa_devolucion`. Escribí lo observado en `NOTAS.md`; ese archivo no se evalúa automáticamente.

**Por qué:** no se arregla lo que no se midió.

**Para qué:** decidir las siguientes limpiezas con evidencia.

**Cómo verificar:** `pytest tests/test_etapa_02_explorar.py`.

## Etapa 3 · Eliminar duplicados

**Qué hacer:** `eliminar_duplicados(df)` devuelve `(tabla_limpia, cantidad_eliminada)`. Quitá únicamente filas idénticas. Dos compras del mismo cliente, misma familia de producto y mismo día pueden ser legítimas si tienen distinto `order_id`.

**Por qué:** una copia pesa dos veces y puede terminar a ambos lados del examen.

**Para qué:** que cada observación cuente una sola vez.

**Cómo verificar:** `pytest tests/test_etapa_03_duplicados.py`.

## Etapa 4 · Tipos y formatos

**Qué hacer:** en `tipos.py`, cada función recibe y devuelve una serie: `convertir_precio`, `convertir_fecha` y `estandarizar_categoria`. Interpretá `1299.90`, `$1,299.90` y `1299,90`; admití fechas `2026-03-14` y `14/03/2026`, dejando `NaT` si son ilegibles; normalizá categorías a minúsculas sin espacios sobrantes.

**Por qué:** un mismo valor escrito de distintas formas no debería contar como valores diferentes.

**Para qué:** validar sobre números y fechas, en vez de texto.

**Cómo verificar:** `pytest tests/test_etapa_04_tipos.py`.

## Etapa 5 · Validar y aplicar reglas de negocio

**Qué hacer:** `validar(df)` devuelve `(filas_validas, cantidad_rechazada)`. Rechazá precios conocidos no positivos, cantidades no positivas y fechas inválidas. Conservá los precios vacíos. `aplicar_reglas(df)` devuelve `(tabla_corregida, cantidad_afectada)` y limita `discount` a [0, 1].

**Por qué:** lo imposible se rechaza; una regla del negocio se hace cumplir en código. Un precio extremo positivo merece investigarse, pero no es imposible por definición.

**Para qué:** evitar que los datos imposibles enseñen al modelo.

**Cómo verificar:** `pytest tests/test_etapa_05_validar.py`.

## Etapa 6 · Valores faltantes

**Qué hacer:** `agregar_indicador_faltante(df, "phone")` devuelve una copia con `phone_missing` (0/1). `comparar_tasa(df, "phone_missing")` devuelve la tasa de devolución por grupo. Compará los resultados. No rellenes `price` todavía.

**Por qué:** un dato que falta puede ser información.

**Para qué:** conservar esa señal y posponer el relleno hasta conocer el entrenamiento.

**Cómo verificar:** `pytest tests/test_etapa_06_faltantes.py`.

## Etapa 7 · Enriquecer sin mirar el futuro

**Qué hacer:** las tres funciones devuelven copias. `dias_desde_registro(df)` agrega los días entre registro y pedido, nunca contra hoy. `precio_unitario(df)` agrega `price/quantity`, cuidando el cero. `quitar_filtracion(df)` elimina `refund_amount` y `return_reason`, incluso si ya estaban ausentes.

**Por qué:** una señal derivada ayuda solo si está disponible al predecir. Un dato creado después de una devolución revela la respuesta.

**Para qué:** dar al modelo señales útiles y legítimas. El test del árbol muestra por qué un resultado casi perfecto puede ser una trampa.

**Cómo verificar:** `pytest tests/test_etapa_07_enriquecer.py`.

## Etapa 8 · Separar y preparar sin filtración

**Qué hacer:** `separar(df)` devuelve `(train, test)`, 80/20, estratificado por `returned`, con `random_state=42`. `construir_pipeline()` devuelve un `ColumnTransformer` sin ajustar. La rama `numericas` usa un `Pipeline` con pasos `imputer` (mediana) y `scaler` (`StandardScaler`) para `price`, `quantity`, `discount`, `phone_missing`, `dias_desde_registro` y `precio_unitario`. La rama `categoricas` usa `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` para `category`, `payment_method` y `shipping_city`. Descartá el resto.

`ajustar_y_transformar(train, test, pipeline)` devuelve dos DataFrames numéricos: mismas columnas de características, `returned` aparte como última columna e índice `order_id`. Excluí `returned` de la entrada del transformador. Ajustá solamente con train, transformá ambos y conservá los nombres de salida. Registrá los tipos de entrada en `pipeline.tipos_entrada_` para el esquema. `version_mal(df)` devuelve `(train_preparado, test_preparado, pipeline)` aprendiendo con todo el dataset antes de separar, a propósito para comparar.

**Por qué:** si la mediana o el escalador ven la prueba, el examen deja de ser limpio. Eso es otra filtración, distinta de mirar reembolsos futuros; su efecto en F1 no siempre es grande.

**Para qué:** obtener matrices comparables sin que la preparación estudie las respuestas del examen.

**Cómo verificar:** `pytest tests/test_etapa_08_pipeline.py`. La mediana de `price` aprendida debe ser la de train, y transformar no debe volver a ajustar.

## Etapa 9 · Cargar y comprobar con producción

**Qué hacer:** `guardar(train, test, pipeline)` escribe `train.csv`, `test.csv`, `preparacion.joblib` y `esquema.json` en `data/processed/`. Los CSV incluyen el índice `order_id`; el esquema contiene `columnas_entrada`, `tipos`, `fecha` UTC y `columnas_salida`. El argumento opcional `destino` permite probar en una carpeta temporal.

`preparar_crudos(orders, customers)` encadena la unión y las etapas 3 a 7. Devuelve `(tabla, registro)` con `leidas`, `unidas`, `duplicadas`, `rechazadas`, `descuentos_limitados` y `procesadas`. Reutilizá las funciones anteriores en el mismo orden que `run_all.py`.

`aplicar_a_nuevos(path)` carga clientes y el joblib, llama a esa preparación y aplica **transform**, sin fit. Devuelve un DataFrame con índice `order_id`, las columnas de características de train (sin `returned`) y el registro en `resultado.attrs["registro"]`. El argumento opcional `artefactos` permite usar otra carpeta de archivos guardados. Producción incluye una categoría nueva: no debería romper la transformación.

**Por qué:** preparar distinto en producción puede cambiar las predicciones sin producir un error.

**Para qué:** dejar datos y preparación reutilizables para el siguiente módulo.

**Cómo verificar:** `pytest tests/test_etapa_09_cargar.py`, luego `python run_all.py`. El programa muestra las filas de cada paso. Los archivos generados no se suben a Git.

## Etapa 10 · Probar que la preparación sirve (opcional)

**Qué hacer:** ejecutá `python evaluar.py` y compartí la última línea del resultado. No hay un test obligatorio para esta etapa.

**Por qué:** una prueba interna excelente puede fallar con pedidos nuevos. Las respuestas de producción están en `.respuestas`, en base64 y en el orden del CSV: es solo para no leerlas a simple vista, no es una medida de seguridad. La evaluación alinea las filas aceptadas por `order_id` e informa las filas rechazadas.

**Para qué:** medir la preparación. El modelo se estudia en **Modelos de clasificación**; acá siempre es `LogisticRegression(max_iter=1000, random_state=42)` con umbral habitual 0,5. F1 combina cuántas devoluciones detectamos y cuántas de las alertas eran correctas. Predecir siempre 0 obtiene F1=0 aunque tenga una exactitud cercana al 80 %.

**Cómo verificar:** `python evaluar.py`. Muestra F1, devoluciones detectadas y exactitud en **Tu prueba** y **Producción**; si la diferencia de F1 supera 0,15, pide revisar la etapa 7. Si faltan archivos, indica la etapa pendiente en español.

## Archivos y recorrido completo

- Datos originales: `data/raw/orders.csv` y `data/raw/customers.json`.
- Pedidos nuevos: `data/new/orders_new.csv`; no traen etiqueta ni datos de devolución.
- Entregables: las funciones completas, `NOTAS.md` con tus decisiones y los cuatro archivos de `data/processed/`.

```bash
python -m pytest
python run_all.py
python evaluar.py
```

En esta clase medimos preparación, no un ranking de personas. Las tasas y los puntajes que veas deben salir de ejecutar tus archivos; no hay resultados prefabricados en este README.
