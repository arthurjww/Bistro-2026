"""Prepara/atualiza o catálogo de músicas usado por app_musicas.py.

Uso normal:
    python baixar_musicas.py

O script consulta o iTunes apenas para músicas ainda não cadastradas ou que estão
sem preview/capa. Votos existentes são preservados.

Para refazer os metadados de todas as músicas:
    python baixar_musicas.py --atualizar
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
from dotenv import load_dotenv
import sys
import time


ROOT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT_DIR.parent
MUSICA_DIR = ROOT_DIR / "backend" / "musica"

load_dotenv(BUNDLE_DIR / ".env")

def resolver_database_path():
    configurado = os.getenv("BISTRO_DATABASE_PATH", "").strip()
    if configurado:
        caminho = Path(configurado).expanduser()
        if not caminho.is_absolute():
            caminho = (BUNDLE_DIR / caminho).resolve()
    else:
        caminho = BUNDLE_DIR / "database" / "bistro.db"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho

DATABASE_PATH = resolver_database_path()

# Permite reaproveitar a lista e a função de consulta existentes no projeto.
sys.path.insert(0, str(MUSICA_DIR))
from musicas import buscar_info_itunes, lista_musicas  # noqa: E402


def criar_tabela(db: sqlite3.Connection) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS musicas (
            num INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            artista TEXT NOT NULL,
            link TEXT,
            capa TEXT,
            estilo TEXT NOT NULL,
            votos INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    colunas = {linha[1] for linha in db.execute("PRAGMA table_info(musicas)")}
    if "votos" not in colunas:
        db.execute("ALTER TABLE musicas ADD COLUMN votos INTEGER DEFAULT 0")
    db.commit()


def remover_duplicatas(db: sqlite3.Connection) -> None:
    grupos = db.execute(
        """
        SELECT LOWER(TRIM(nome)), LOWER(TRIM(estilo)), MIN(num), SUM(COALESCE(votos, 0))
        FROM musicas
        GROUP BY LOWER(TRIM(nome)), LOWER(TRIM(estilo))
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    for nome_norm, estilo_norm, manter_num, total_votos in grupos:
        db.execute("UPDATE musicas SET votos = ? WHERE num = ?", (total_votos, manter_num))
        db.execute(
            """
            DELETE FROM musicas
            WHERE LOWER(TRIM(nome)) = ?
              AND LOWER(TRIM(estilo)) = ?
              AND num <> ?
            """,
            (nome_norm, estilo_norm, manter_num),
        )
    db.commit()


def preparar_catalogo(atualizar: bool = False, intervalo: float = 1.0) -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH, timeout=30) as db:
        db.execute("PRAGMA busy_timeout = 30000")
        try:
            db.execute("PRAGMA journal_mode = WAL")
        except sqlite3.DatabaseError:
            pass
        criar_tabela(db)
        remover_duplicatas(db)

        catalogo = lista_musicas()
        total = len(catalogo)
        consultadas = 0
        ignoradas = 0
        inseridas = 0
        atualizadas = 0
        falhas = 0

        print(f"Banco: {DATABASE_PATH}")
        print(f"Catálogo: {total} músicas")
        print("Consultando o iTunes somente quando necessário...\n")

        for indice, (nome, artista, estilo) in enumerate(catalogo, start=1):
            existente = db.execute(
                """
                SELECT num, link, capa
                FROM musicas
                WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
                  AND LOWER(TRIM(estilo)) = LOWER(TRIM(?))
                LIMIT 1
                """,
                (nome, estilo),
            ).fetchone()

            # No modo normal, uma música já completa não faz nova requisição.
            if existente and not atualizar and existente[1] and existente[2]:
                ignoradas += 1
                print(f"[{indice}/{total}] OK (já cadastrada): {nome} - {artista}")
                continue

            consultadas += 1
            try:
                link_preview, link_capa = buscar_info_itunes(nome, artista)
            except Exception as exc:
                link_preview, link_capa = "", ""
                print(f"[{indice}/{total}] ERRO: {nome} - {artista}: {exc}")

            if not link_preview and not link_capa:
                falhas += 1

            if existente:
                # Mantém os votos; altera apenas os dados da música/metadados.
                link_final = link_preview or existente[1] or ""
                capa_final = link_capa or existente[2] or ""
                db.execute(
                    """
                    UPDATE musicas
                    SET nome = ?, artista = ?, estilo = ?, link = ?, capa = ?
                    WHERE num = ?
                    """,
                    (nome, artista, estilo, link_final, capa_final, existente[0]),
                )
                atualizadas += 1
                acao = "atualizada"
            else:
                db.execute(
                    """
                    INSERT INTO musicas (nome, artista, link, capa, estilo, votos)
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (nome, artista, link_preview, link_capa, estilo),
                )
                inseridas += 1
                acao = "cadastrada"

            db.commit()
            print(f"[{indice}/{total}] {acao}: {nome} - {artista}")

            if intervalo > 0 and indice < total:
                time.sleep(intervalo)

        print("\nConcluído.")
        print(f"  Novas: {inseridas}")
        print(f"  Atualizadas: {atualizadas}")
        print(f"  Já prontas/ignoradas: {ignoradas}")
        print(f"  Consultas ao iTunes: {consultadas}")
        print(f"  Sem resultado de preview/capa: {falhas}")
        print("\nAgora inicie o site com: python app_musicas.py")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa/prepara os metadados das músicas para o sistema de votação."
    )
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="consulta novamente o iTunes para todas as músicas, preservando os votos",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="segundos entre consultas ao iTunes (padrão: 1.0)",
    )
    args = parser.parse_args()

    preparar_catalogo(
        atualizar=args.atualizar,
        intervalo=max(0.0, args.intervalo),
    )


if __name__ == "__main__":
    main()
