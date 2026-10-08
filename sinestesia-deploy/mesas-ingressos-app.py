"""Launcher principal do sistema de mesas e ingressos.

Este arquivo fica na raiz de propósito. Todos os serviços leem o mesmo .env e
usam o mesmo database/bistro.db.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
SERVICE_DIR = ROOT_DIR / "mesas-ingressos"

# Um único .env, sempre o da raiz.
load_dotenv(ROOT_DIR / ".env", override=True)

# O código original usa imports como `from backend import ...`.
sys.path.insert(0, str(SERVICE_DIR))

from backend import app  # noqa: E402
from backend.banco_de_dados import create_all  # noqa: E402
from backend.mapa_mesas.lugares import MapaLugares  # noqa: E402


def preparar_banco() -> None:
    """Cria/migra estrutura e garante os lugares, sem apagar dados."""
    with app.app_context():
        create_all()
        MapaLugares().seed_lugares()


preparar_banco()


if __name__ == "__main__":
    app.run(
        host=os.getenv("INGRESSOS_HOST", "127.0.0.1"),
        port=int(os.getenv("INGRESSOS_PORT", "8080")),
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"},
    )
