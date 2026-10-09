"""Executa o downloader incremental de músicas usando o .env e DB da raiz."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
runpy.run_path(str(ROOT_DIR / "musicas" / "baixar_musicas.py"), run_name="__main__")
