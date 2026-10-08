"""Cria um administrador no banco compartilhado do Sinestesia Bistrô."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
runpy.run_path(str(ROOT_DIR / "relatorios" / "criar_admin_relatorios.py"), run_name="__main__")
