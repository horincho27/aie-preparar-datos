# Tienda Nimbus · Preparar datos para entrenamiento

Nimbus es una tienda ficticia. Vas a preparar sus pedidos para estimar si un pedido nuevo se devolverá. En los pedidos históricos, `returned=1` significa que se devolvió y `returned=0` que no. Construye tu preparación desde cero con el agente de IA y usa la balanza para observar el efecto de cada cambio. La práctica termina cuando revisas tus resultados en clase.

## Empieza en VS Code local (Windows)

Abre la carpeta del repositorio en VS Code. Necesitas Python 3.12 y las extensiones **Python** y **Jupyter** de VS Code. Los datos ya están en el repositorio.

1. Abre una terminal de PowerShell en la carpeta principal del proyecto. Crea y activa el entorno.

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Si PowerShell bloquea la activación por permisos, ejecuta `Set-ExecutionPolicy -Scope Process Bypass` en esa terminal y vuelve a ejecutar `.\.venv\Scripts\Activate.ps1`. El cambio solo dura hasta que cierres esa terminal. [Políticas de ejecución de PowerShell](https://learn.microsoft.com/powershell/module/microsoft.powershell.security/set-executionpolicy)

2. Instala las dependencias en la misma terminal, con `.venv` activo.

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Abre [notebooks/practica.ipynb](notebooks/practica.ipynb). En la esquina superior derecha, elige **Seleccionar kernel → Entornos de Python → .venv**. Si ya aparece otro kernel, haz clic en su nombre y elige **Seleccionar otro kernel**. [Selector de kernel de VS Code](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management)
4. Ejecuta la primera celda. Esa celda lee y une los datos crudos. Las demás celdas de código están vacías para que trabajes en ellas.

### Alternativa en Codespaces

Abre **Code → Codespaces → Create codespace**. El entorno instala las dependencias de `requirements.txt`. Abre [notebooks/practica.ipynb](notebooks/practica.ipynb), selecciona el kernel de Python 3.12 y ejecuta la primera celda.

## Primer mensaje para tu agente

Abre la extensión de IA de la academia y copia el mensaje de tu etapa. Ejecuta tú el código de exploración en una celda nueva y pega el resultado en el chat antes de pedir cambios.

**Etapa 0 · Primera medición**

```text
Lee CONTEXTO.md. Estoy en la etapa 0. Dame el código para ver cómo llegan los datos antes de medir.
```

**Etapa 1 · Limpieza**

```text
Lee CONTEXTO.md. Estoy en la etapa 1. Dame el código para explorar los datos antes de proponer cambios.
```

**Etapa 2 · La columna que hace trampa**

```text
Lee CONTEXTO.md. Estoy en la etapa 2. Dame el código para comparar las columnas de los pedidos históricos y nuevos.
```

**Etapa 3 · El dato que falta**

```text
Lee CONTEXTO.md. Estoy en la etapa 3. Dame el código para ver cuántos pedidos tienen el teléfono vacío.
```

**Etapa 4 · Ajuste y transformación**

```text
Lee CONTEXTO.md. Estoy en la etapa 4. Dame el código para revisar los tipos de las columnas y cuántos precios están vacíos.
```

## Cómo usar la balanza

Escribe una función `preparar(tabla)` en el notebook. Recibe una tabla de pandas y devuelve otra con tus cambios. Conserva `order_id` para seguir cada pedido y `returned` en el histórico. La balanza usa la misma función con pedidos nuevos y compara sus predicciones con respuestas guardadas aparte.

Ejecuta `medir(preparar, etapa=0)` y cambia el número según tu avance. La balanza usa la misma regresión logística en todas las etapas y da más peso a la clase menos frecuente en entrenamiento. Sin transformador, usa las columnas numéricas de train. Si faltan campos en producción, los trata como vacíos. Usa cero para los vacíos numéricos solo al medir, sin cambiar las tablas que devolviste. En la etapa 4, tu transformador se ocupa de los vacíos.

Lee las entradas elegidas y el diagnóstico de texto y vacíos. Si la medición se guarda, podrás comparar el antes y el ahora en pantalla y revisar el historial en `mediciones.csv`. Para verificar el resultado, usa `python evaluar.py N` en la terminal de la raíz y sustituye `N` por tu etapa. `python evaluar.py` revisa hasta la etapa 4.

## Etapa 0 · Haz una primera medición

- **Qué lograr y por qué.** Observa cómo son los pedidos antes de prepararlos. Una primera medición te da un punto de comparación.
- **Qué debe quedar.** Una medición guardada con `etapa=0`. Conserva el identificador y la etiqueta histórica.
- **Cómo medir.** Ejecuta `medir(lambda tabla: tabla, etapa=0)`. Esta función devuelve la tabla tal cual. Lee el diagnóstico y guarda este resultado como punto de comparación.
- **Cómo verificar.** Ejecuta `python evaluar.py 0`.

## Etapa 1 · Limpia y valida

- **Qué lograr y por qué.** Elimina copias exactas y conserva compras legítimas con otro identificador. Convierte precios y fechas para que se puedan comparar. Unifica categorías en minúsculas y sin espacios en los bordes. Aplica las reglas de negocio para precios, fechas y descuentos.
- **Qué debe quedar.** `price` numérico, `order_date` como fecha, categorías coherentes, precios conocidos positivos y descuentos entre 0 y 1. Conserva los precios que ya estaban vacíos y las columnas originales de cada tabla. Si un precio es menor o igual a 0 o la fecha es ilegible, quita el pedido. Si un descuento sale de 0 a 1, llévalo al borde sin quitar el pedido.
- **Cómo medir.** Ejecuta `medir(preparar, etapa=1)` con tu función actualizada. Compara el número de filas y el F1 con tu medición anterior. Si la balanza indica que el modelo aún recibe información que adelanta la respuesta, investígala en la etapa 2.
- **Cómo verificar.** Ejecuta `python evaluar.py 1`. Lee cuántas filas salieron.

## Etapa 2 · La columna que hace trampa

- **Qué lograr y por qué.** Calcula los días entre el registro y el pedido. Revisa qué campos existirían al llegar un pedido nuevo. La información posterior puede hacer que la prueba parezca excelente y fallar al predecir.
- **Qué debe quedar.** `dias_desde_registro` calculado respecto de la fecha del pedido y una preparación que produzca el mismo resultado al repetirla. Quita los datos que solo existen después de la devolución. Conserva la etiqueta en el histórico.
- **Cómo medir.** Ejecuta `medir(preparar, etapa=2)`. Compara lo que ocurre en prueba y producción.
- **Cómo verificar.** Ejecuta `python evaluar.py 2`. Si falta una etapa previa, el verificador te indica cuál.

## Etapa 3 · El dato que falta

- **Qué lograr y por qué.** Marca si falta el teléfono. La ausencia de un dato puede ser una señal útil.
- **Qué debe quedar.** `phone_missing` vale 1 si falta el teléfono y 0 si está presente, tanto en el histórico como en producción.
- **Cómo medir.** Ejecuta `medir(preparar, etapa=3)` y compara los puntajes con la medición de la etapa 2.
- **Cómo verificar.** Ejecuta `python evaluar.py 3`. Compara la tasa de devolución de los dos grupos.

## Etapa 4 · Ajusta con entrenamiento y transforma

- **Qué lograr y por qué.** Define un transformador de scikit-learn que pueda aprender un valor para rellenar precios, normalizar variables numéricas y codificar categorías. La prueba queda separada de lo que se aprende.
- **Qué debe quedar.** Tu función prepara cada tabla del mismo modo y el transformador se pasa sin ajustar. La balanza separa 80/20 de forma estratificada, ajusta solo con train y usa `transform` con prueba y producción. La preparación aprendida queda en `data/processed/preparacion.joblib`.
- **Cómo medir.** Ejecuta `medir(preparar, etapa=4, transformador=transformador)`. Revisa qué columnas entran al modelo y cuáles son nuevas. Las entradas y su representación pueden cambiar el F1. Ajustar solo con train mantiene separada la prueba.
- **Cómo verificar.** Ejecuta `python evaluar.py 4`. Comprueba el ajuste guardado, la separación y que producción se pueda transformar con su categoría nueva.

## Lee los resultados

- **F1.** Combina cuántas devoluciones encuentras y qué proporción de tus alertas son correctas. Cuanto más alto, mejor es ese equilibrio.
- **Detectadas.** «13 de 33» quiere decir que encontraste 13 de las 33 devoluciones reales.
- **Exactitud.** Cuenta todos los aciertos. Si la mayoría de los pedidos no se devuelve, predecir siempre que no hay devolución puede acertar mucho y detectar cero devoluciones.

Si quieres, anota una observación por etapa y comenta en voz alta qué cambio tuvo mayor efecto. [NOTAS.md](NOTAS.md)
