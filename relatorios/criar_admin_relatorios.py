"""Cria um administrador no banco compartilhado dos sistemas do Bistrô."""

import getpass
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT_DIR.parent
load_dotenv(BUNDLE_DIR / ".env")


def database_path():
    configurado = os.getenv("BISTRO_DATABASE_PATH", "").strip()
    if configurado:
        p = Path(configurado).expanduser()
        return p if p.is_absolute() else (BUNDLE_DIR / p).resolve()
    return BUNDLE_DIR / "database" / "bistro.db"


def main():
    nome = input("Nome do administrador: ").strip()
    email = input("E-mail: ").strip().lower()
    senha = getpass.getpass("Senha: ")
    confirmar = getpass.getpass("Confirme a senha: ")

    if not nome or not email or not senha:
        raise SystemExit("Nome, e-mail e senha são obrigatórios.")
    if senha != confirmar:
        raise SystemExit("As senhas não coincidem.")

    caminho = database_path()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(caminho, timeout=30) as db:
        db.execute("PRAGMA busy_timeout = 30000")
        existente = db.execute(
            "SELECT cod_admin FROM Administradores WHERE LOWER(email) = ?",
            (email,),
        ).fetchone()
        if existente:
            raise SystemExit("Já existe um administrador com esse e-mail.")
        db.execute(
            "INSERT INTO Administradores(nome_admin, senha, email) VALUES (?, ?, ?)",
            (nome, generate_password_hash(senha), email),
        )
        db.commit()

    print(f"Administrador criado com sucesso em: {caminho}")


if __name__ == "__main__":
    main()
