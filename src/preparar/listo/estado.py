# Traduce una función pendiente a un mensaje con el número de etapa.
# Corresponde al acompañamiento de la práctica: no cambia los datos.

class EtapaPendiente(NotImplementedError):
    """Permite mostrar una indicación útil sin un error técnico en pantalla."""

    def __init__(self, numero):
        nombres = {1: "el dato que falta", 2: "la columna que hace trampa", 3: "separar y preparar sin filtración"}
        super().__init__(f"Falta completar la etapa {numero}: {nombres[numero]}. Revisá sus funciones y tests.")


def ejecutar_etapa(numero, funcion, *argumentos):
    """Llama una función del alumno e identifica su etapa si todavía está vacía."""
    try:
        return funcion(*argumentos)
    except NotImplementedError as error:
        raise EtapaPendiente(numero) from error
