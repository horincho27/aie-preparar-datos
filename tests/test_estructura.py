"""La estructura y los datos están disponibles desde la base preparada."""
import base64
import importlib
import json
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

def test_archivos_e_importaciones():
    for nombre in ["faltantes", "enriquecer", "pipeline", "listo.extraer", "listo.explorar", "listo.duplicados", "listo.tipos", "listo.validar", "listo.enriquecer", "listo.pipeline", "listo.cargar", "listo.estado", "listo.recorrido"]:
        assert importlib.import_module(f"preparar.{nombre}") is not None
    for nombre in ["README.md", "NOTAS.md", "requirements.txt", "run_all.py", "evaluar.py", ".devcontainer/devcontainer.json", "data/processed/.gitkeep", "src/preparar/listo/LEEME.md"]:
        assert (RAIZ / nombre).is_file()

def test_datos_presentes_y_sin_etiqueta_en_produccion():
    pedidos = pd.read_csv(RAIZ / "data/raw/orders.csv")
    nuevos = pd.read_csv(RAIZ / "data/new/orders_new.csv")
    clientes = json.loads((RAIZ / "data/raw/customers.json").read_text(encoding="utf-8"))
    assert len(pedidos) == 2040 and len(nuevos) == 200 and len(clientes) == 400
    assert {"returned", "refund_amount", "return_reason"}.isdisjoint(nuevos.columns)
    assert set(nuevos.columns) == set(pedidos.columns) - {"returned", "refund_amount", "return_reason"}

def test_respuestas_codificadas_en_orden():
    respuestas = json.loads(base64.b64decode((RAIZ / "data/new/.respuestas").read_bytes()))
    assert len(respuestas) == 200 and set(respuestas) == {0, 1}
    assert 0.15 <= sum(respuestas) / len(respuestas) <= 0.25


def test_solo_tres_archivos_de_trabajo():
    nombres = {p.name for p in (RAIZ / "src/preparar").glob("*.py")} - {"__init__.py"}
    assert nombres == {"faltantes.py", "enriquecer.py", "pipeline.py"}
