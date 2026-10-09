"""Launcher principal do painel de relatórios/administração.

Nginx pode publicar este serviço como admin.sinestesiabistro.com.br.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
SERVICE_DIR = ROOT_DIR / "relatorios"

load_dotenv(ROOT_DIR / ".env", override=True)
sys.path.insert(0, str(SERVICE_DIR))

from backend.relatorios import app  # noqa: E402


if __name__ == "__main__":
    app.run(
        host=os.getenv("RELATORIOS_HOST", "127.0.0.1"),
        port=5003,
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"},
    )
