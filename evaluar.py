"""Muestra el efecto de las etapas completas con un mismo modelo."""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from preparar.listo.reporte import mostrar_reportes


def main():
    try:
        mostrar_reportes(RAIZ)
    except FileNotFoundError:
        print("Faltan archivos del proyecto. Revisa las carpetas data y src/preparar/listo.")
    except (ValueError, KeyError):
        print("Los datos de la evaluación no coinciden con lo esperado. Revisa los archivos del proyecto y ejecuta las pruebas.")


if __name__ == "__main__":
    main()
