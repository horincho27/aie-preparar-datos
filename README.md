# Preparar datos · Tienda Nimbus · versión corta

Esta práctica tiene tres etapas. Nimbus es una tienda ficticia de ropa, electrónica, hogar y libros. Vas a preparar los datos para predecir más adelante si un pedido se devolverá. `returned=1` indica devolución y `returned=0` indica que el pedido no se devolvió.

Completa **seis funciones en tres archivos**. Puedes leer el resto del código ya resuelto. El repositorio incluye datos inventados de 2.040 filas históricas, 400 clientes y 200 pedidos nuevos. No necesitas descargar datos ni conectarte a una API.

## Preparar el entorno

Abre **Code → Codespaces → Create codespace**. El entorno usa Python 3.12 e instala las versiones fijadas de `requirements.txt`.

```bash
python -m pip install -r requirements.txt
python -m pytest
```

En tu equipo, crea un entorno con `python -m venv .venv`. Actívalo con `source .venv/bin/activate` en Linux/macOS o `.venv\Scripts\Activate.ps1` en PowerShell. Después instala los requisitos. Una vez instalados, todos los tests corren sin internet y en menos de 30 segundos.

Al principio pasan 20 pruebas y fallan 10. Es lo esperado mientras las funciones de las tres etapas están vacías. Ejecuta solo las pruebas de la etapa en curso. Para la etapa 1, usa `pytest tests/test_etapa_1_faltantes.py`. Cada fallo ocupa una línea. Para ver el detalle completo, ejecuta `pytest --tb=long`.

No hace falta modificar las pruebas ni el modelo de evaluación. Si quieres, anota lo que observes en [NOTAS.md](NOTAS.md).

## Lo que ya está hecho

Lee el recorrido completo para ubicar la lectura y unión, la exploración, los duplicados, los tipos y formatos, la validación, las reglas de negocio, el precio unitario, el ajuste del transformador, el guardado y la aplicación a producción. [src/preparar/listo/LEEME.md](src/preparar/listo/LEEME.md)

**Los precios vacíos se conservan:** se rellenan en la etapa 3 con una mediana aprendida solo del entrenamiento. `price` es el importe del pedido antes del descuento, `quantity` la cantidad de unidades y `discount` una proporción. Los datos se unen por `customer_id`; `order_id` identifica pedidos y nunca es una característica del modelo.

```bash
pytest tests/test_listo.py tests/test_estructura.py
```

## Etapa 1 · El dato que falta

**Qué hacer.** Completa `src/preparar/faltantes.py`. `agregar_indicador_faltante(df, columna)` recibe una tabla y el nombre `"phone"`. Devuelve una copia con `phone_missing`, de valor 1 si falta el teléfono y 0 si está. `comparar_tasa(df, columna)` recibe esa tabla y `"phone_missing"`. Devuelve un diccionario con la tasa de `returned` por grupo (claves 0 y 1). Compara las tasas. No rellenes el precio.

**Por qué:** un dato que falta puede ser información.

**Para qué:** conservar la señal más fuerte de estos datos en vez de perderla al rellenar ausencias.

**Cómo verificar:** `pytest tests/test_etapa_1_faltantes.py`. Debe existir el indicador, valer 0 o 1 y mostrar una tasa mayor en el grupo sin teléfono.

## Etapa 2 · La columna que hace trampa

**Qué hacer.** Completa `src/preparar/enriquecer.py`. `dias_desde_registro(df)` devuelve una copia con los días entre `signup_date` y `order_date`. Usa la fecha del pedido para el cálculo. El precio por unidad ya lo calcula una función de `listo/`.

`quitar_filtracion(df)` devuelve una copia sin las columnas que solo existen después de que el pedido se devolvió. Para encontrarlas, revisa cada columna de `data/raw` y pregúntate si existiría cuando llega un pedido nuevo. Debe funcionar aunque esas columnas ya falten, como ocurre en producción.

**Por qué:** una columna creada después de la devolución le regala la respuesta al modelo.

**Para qué:** aprender con información que existe cuando llega el pedido, sin mirar el futuro.

**Cómo verificar.** Ejecuta `pytest tests/test_etapa_2_filtracion.py` para comprobar el cálculo de días y la eliminación de las columnas del futuro. Observa cómo esos datos afectan al resultado de un árbol simple.

## Etapa 3 · Separar y preparar sin filtración

**Qué hacer.** Completa `src/preparar/pipeline.py`. `separar(df)` devuelve `(train, test)`, 80/20, estratificado por `returned`, con `random_state=42`. `construir_pipeline()` devuelve un `ColumnTransformer` **sin ajustar** con dos ramas.

- `numericas`: un `Pipeline` con pasos `imputer` (`SimpleImputer(strategy="median")`) y `scaler` (`StandardScaler`), para `price`, `quantity`, `discount`, `phone_missing`, `dias_desde_registro` y `precio_unitario`.
- `categoricas`: `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` para `category`, `payment_method` y `shipping_city`.

Descarta el resto de las columnas. La función resuelta `listo.pipeline.ajustar_y_transformar` excluye la etiqueta, ajusta **solo con train** y transforma train/test conservando sus nombres. Los tests esperan los nombres de ramas y pasos indicados arriba. Para comparar en clase, `listo.pipeline.version_mal(df)` viene resuelta y ajusta antes de separar.

**Por qué:** si la mediana o el escalador ven la prueba, el examen deja de ser limpio. Esta filtración es distinta de conservar datos del futuro; su efecto en F1 no siempre es grande.

**Para qué:** obtener datos preparados y medir su utilidad sin trampa.

**Cómo verificar.** Ejecuta `pytest tests/test_etapa_3_sin_filtracion.py` para comprobar la mediana de train y que transformar no reajuste. Después ejecuta las pruebas completas y el evaluador.

```bash
python -m pytest
python evaluar.py
```

Si quieres recorrer la preparación completa, ejecuta `python run_all.py`. El comando muestra las filas de cada paso y guarda `train.csv`, `test.csv`, `preparacion.joblib` y `esquema.json` en `data/processed/`. Los nuevos pedidos atraviesan la misma limpieza y tus etapas 1 y 2. El transformador guardado se aplica con `transform`, sin un nuevo ajuste. Una categoría desconocida no debe romper la preparación.

## Cómo leer la evaluación

`python evaluar.py` muestra el antes y el después de cada etapa completa. Usa siempre `LogisticRegression(max_iter=1000, random_state=42)` y mantiene las otras etapas fijas con la referencia de `listo/`. El modelo se estudia en **Modelos de clasificación**. En esta práctica se mide el efecto de la preparación.

- **F1:** puntaje principal; combina cuántas devoluciones detectamos y cuántas alertas eran correctas.
- **Devoluciones detectadas:** cuántas encontró entre todas las devoluciones reales, por ejemplo «13 de 33».
- **Exactitud.** Proporción total de aciertos. En producción, predecir que ningún pedido se devuelve acierta más del 83 % y detecta cero devoluciones. Su F1 es 0.

Ejecuta el evaluador después de cada etapa para ver el antes y el después. Si hay funciones pendientes, el comando indica la primera etapa que falta. Cuando las tres están completas, aparece una tabla con las filas «Correcta», «Con datos del futuro» y «Siempre cero». El evaluador calcula el informe desde los datos originales.

Las respuestas de producción están en `data/new/.respuestas`, en base64 y en el orden del CSV. Eso solo evita leerlas a simple vista; no es seguridad. La evaluación alinea por `order_id` después de rechazar filas e informa cuántas fueron evaluadas.

La práctica termina cuando ves el antes y el después de las tres etapas en el evaluador. Comparte en voz alta en clase la última línea **«Mi F1 en producción: 0,XX»**.
