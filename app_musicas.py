"""Launcher principal da votação de músicas.

Expõe a variável `app` para Flask/Gunicorn e lê somente o .env da raiz.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
SERVICE_FILE = ROOT_DIR / "musicas" / "webapp.py"

load_dotenv(ROOT_DIR / ".env", override=True)

spec = importlib.util.spec_from_file_location("sinestesia_musicas_webapp", SERVICE_FILE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Não foi possível carregar {SERVICE_FILE}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app


if __name__ == "__main__":
    app.run(
        host=os.getenv("MUSICAS_HOST", "127.0.0.1"),
        port=int(os.getenv("MUSICAS_PORT", "4444")),
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"},
    )
