# Preparar datos · Tienda Nimbus · versión corta

Una práctica de tres etapas para una clase de una hora. Nimbus es una tienda ficticia de ropa, electrónica, hogar y libros. Queremos preparar los datos para predecir más adelante si un pedido se devolverá: `returned=1` indica devolución y `returned=0` que no.

Vas a completar **seis funciones en tres archivos**. El resto viene resuelto para leerlo. Los datos son los mismos de la versión larga: 2.040 filas históricas, 400 clientes y 200 pedidos nuevos. Son inventados y están en el repositorio; no necesitás descargar datasets ni conectarte a una API.

## Preparar el entorno

Abrí **Code → Codespaces → Create codespace**. El entorno usa Python 3.12 e instala las versiones fijadas de `requirements.txt`.

```bash
python -m pip install -r requirements.txt
python -m pytest
```

Localmente, creá un entorno con `python -m venv .venv` y activalo: `source .venv/bin/activate` en Linux/macOS o `.venv\Scripts\Activate.ps1` en PowerShell. Después instalá los requisitos. Una vez instalados, todos los tests corren sin internet y en menos de 30 segundos.

Al principio pasan `tests/test_listo.py` y `tests/test_estructura.py`; las pruebas de las tres etapas fallan porque sus funciones están vacías. No hace falta modificar tests ni el modelo de evaluación. Anotá tus decisiones en `NOTAS.md`.

## Lo que ya está hecho

Leé [src/preparar/listo/LEEME.md](src/preparar/listo/LEEME.md): explica la tubería completa, en orden. Ahí están resueltos la lectura y unión, exploración, duplicados, tipos y formatos, validación, reglas de negocio, precio unitario, ajuste del transformador, guardado y aplicación a producción.

**Los precios vacíos se conservan:** se rellenan en la etapa 3 con una mediana aprendida solo del entrenamiento. `price` es el importe del pedido antes del descuento, `quantity` la cantidad de unidades y `discount` una proporción. Los datos se unen por `customer_id`; `order_id` identifica pedidos y nunca es una característica del modelo.

```bash
pytest tests/test_listo.py tests/test_estructura.py
```

## Etapa 1 · El dato que falta

**Qué hacer:** completá `src/preparar/faltantes.py`. `agregar_indicador_faltante(df, columna)` recibe una tabla y el nombre `"phone"`; devuelve una copia con `phone_missing`, de valor 1 si falta el teléfono y 0 si está. `comparar_tasa(df, columna)` recibe esa tabla y `"phone_missing"`; devuelve un diccionario con la tasa de `returned` por grupo (claves 0 y 1). Compará las tasas. No rellenes el precio.

**Por qué:** un dato que falta puede ser información.

**Para qué:** conservar la señal más fuerte de estos datos en vez de perderla al rellenar ausencias.

**Cómo verificar:** `pytest tests/test_etapa_1_faltantes.py`. Debe existir el indicador, valer 0 o 1 y mostrar una tasa mayor en el grupo sin teléfono.

## Etapa 2 · La columna que hace trampa

**Qué hacer:** completá `src/preparar/enriquecer.py`. `dias_desde_registro(df)` devuelve una copia con los días entre `signup_date` y `order_date`; nunca uses la fecha de hoy. `quitar_filtracion(df)` devuelve una copia sin `refund_amount` ni `return_reason`, incluso si esas columnas ya faltan, como ocurre en producción. El precio por unidad ya lo calcula una función de `listo/`.

**Por qué:** una columna creada después de la devolución le regala la respuesta al modelo.

**Para qué:** aprender con información que existe cuando llega el pedido, sin mirar el futuro.

**Cómo verificar:** `pytest tests/test_etapa_2_filtracion.py`. Comprueba los días, la eliminación de ambas columnas y la trampa: un árbol simple con el reembolso acierta casi el 100 %, pero sin él no.

## Etapa 3 · Separar y preparar sin filtración

**Qué hacer:** completá `src/preparar/pipeline.py`. `separar(df)` devuelve `(train, test)`, 80/20, estratificado por `returned`, con `random_state=42`. `construir_pipeline()` devuelve un `ColumnTransformer` **sin ajustar**, con estas ramas:

- `numericas`: un `Pipeline` con pasos `imputer` (`SimpleImputer(strategy="median")`) y `scaler` (`StandardScaler`), para `price`, `quantity`, `discount`, `phone_missing`, `dias_desde_registro` y `precio_unitario`.
- `categoricas`: `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` para `category`, `payment_method` y `shipping_city`.

Descartá el resto de las columnas. La función resuelta `listo.pipeline.ajustar_y_transformar` excluye la etiqueta, ajusta **solo con train** y transforma train/test conservando sus nombres. Los tests esperan los nombres de ramas y pasos indicados arriba. Para comparar en clase, `listo.pipeline.version_mal(df)` viene resuelta y ajusta antes de separar.

**Por qué:** si la mediana o el escalador ven la prueba, el examen deja de ser limpio. Esta filtración es distinta de conservar datos del futuro; su efecto en F1 no siempre es grande.

**Para qué:** obtener datos preparados y medir su utilidad sin trampa.

**Cómo verificar:** `pytest tests/test_etapa_3_sin_filtracion.py`. Comprueba la mediana de train y que transformar no reajuste. Después ejecutá:

```bash
python -m pytest
python run_all.py
python evaluar.py
```

`run_all.py` muestra las filas de cada paso y guarda `train.csv`, `test.csv`, `preparacion.joblib` y `esquema.json` en `data/processed/`. Los nuevos pedidos atraviesan la misma limpieza y tus etapas 1 y 2; el transformador guardado se aplica con `transform`, sin un nuevo ajuste. Una categoría desconocida no debe romper la preparación.

## Cómo leer la evaluación

`python evaluar.py` compara **Tu prueba** con **Producción** usando siempre `LogisticRegression(max_iter=1000, random_state=42)`. El modelo se estudia en **Modelos de clasificación**; hoy medimos preparación, no elegimos algoritmos.

- **F1:** puntaje principal; combina cuántas devoluciones detectamos y cuántas alertas eran correctas.
- **Devoluciones detectadas:** cuántas encontró entre todas las devoluciones reales, por ejemplo «13 de 33».
- **Exactitud:** proporción total de aciertos. Sola engaña: decir «nadie devuelve» ya acierta alrededor del 80 %, pero detecta cero devoluciones y obtiene F1=0.

Si el F1 de prueba supera al de producción por más de 0,15, el programa pide revisar la etapa 2. Si falta una función, indica cuál de las tres etapas está pendiente, en español. Cuando las tres estén completas, si faltan los archivos guardados, pide correr `run_all.py`.

Las respuestas de producción están en `data/new/.respuestas`, en base64 y en el orden del CSV. Eso solo evita leerlas a simple vista; no es seguridad. La evaluación alinea por `order_id` después de rechazar filas e informa cuántas fueron evaluadas.

Compartí la última línea: **«Mi F1 en producción: 0,XX»**. Entregá las seis funciones, tus decisiones en `NOTAS.md` y los cuatro archivos generados de `data/processed/` por el medio indicado por el docente; esos archivos están ignorados por Git.
