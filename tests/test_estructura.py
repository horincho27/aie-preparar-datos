"""Estas pruebas pasan desde la etapa 0, también en el repositorio de alumnos."""
import base64
import importlib
import json
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

def test_archivos_e_importaciones():
    for nombre in ["extraer", "explorar", "duplicados", "tipos", "validar", "faltantes", "enriquecer", "pipeline", "cargar"]:
        assert importlib.import_module(f"preparar.{nombre}") is not None
    for nombre in ["README.md", "NOTAS.md", "requirements.txt", "run_all.py", "evaluar.py", ".devcontainer/devcontainer.json", "data/processed/.gitkeep"]:
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
