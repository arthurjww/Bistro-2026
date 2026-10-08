"""Aplicação web da votação de músicas usando o banco compartilhado do Bistrô."""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, render_template, request

ROOT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT_DIR.parent
TEMPLATE_DIR = ROOT_DIR / "frontend" / "templates" / "musicas"

load_dotenv(BUNDLE_DIR / ".env")


def resolver_database_path() -> Path:
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

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
app.config["DATABASE"] = str(DATABASE_PATH)


def get_db():
    db = getattr(g, "_musicas_database", None)
    if db is None:
        db = g._musicas_database = sqlite3.connect(
            app.config["DATABASE"], timeout=30
        )
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        db.execute("PRAGMA foreign_keys = ON")
    return db


@app.teardown_appcontext
def close_connection(_exception=None):
    db = getattr(g, "_musicas_database", None)
    if db is not None:
        db.close()


def inicializar_banco():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH, timeout=30) as db:
        db.execute("PRAGMA busy_timeout = 30000")
        try:
            db.execute("PRAGMA journal_mode = WAL")
        except sqlite3.DatabaseError:
            pass
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
        db.execute("CREATE INDEX IF NOT EXISTS idx_musicas_votos ON musicas(votos DESC)")
        db.commit()


def carregar_enquetes(db):
    estilos = [
        row["estilo"]
        for row in db.execute(
            "SELECT DISTINCT estilo FROM musicas ORDER BY estilo COLLATE NOCASE"
        ).fetchall()
    ]
    enquetes = {}
    for estilo in estilos:
        enquetes[estilo] = db.execute(
            """
            SELECT num, nome, artista, link, capa, estilo, COALESCE(votos, 0) AS votos
            FROM musicas
            WHERE estilo = ?
            ORDER BY votos DESC, nome COLLATE NOCASE ASC
            """,
            (estilo,),
        ).fetchall()
    return estilos, enquetes


@app.route("/", methods=["GET", "POST"])
def votacao():
    mensagem = ""
    mostrar_resultados = False
    db = get_db()
    estilos, _ = carregar_enquetes(db)

    if request.method == "POST":
        votos_recebidos = {}
        for estilo in estilos:
            musica_id = request.form.get(estilo, "").strip()
            if not musica_id:
                mensagem = "Por favor, escolha uma opção em TODAS as enquetes antes de enviar!"
                break
            musica = db.execute(
                "SELECT num FROM musicas WHERE num = ? AND estilo = ?",
                (musica_id, estilo),
            ).fetchone()
            if musica is None:
                mensagem = "Foi recebido um voto inválido. Atualize a página e tente novamente."
                break
            votos_recebidos[estilo] = musica_id

        if not mensagem and estilos:
            try:
                for musica_id in votos_recebidos.values():
                    db.execute(
                        "UPDATE musicas SET votos = COALESCE(votos, 0) + 1 WHERE num = ?",
                        (musica_id,),
                    )
                db.commit()
                mensagem = "Seus votos foram registrados com sucesso!"
                mostrar_resultados = True
            except sqlite3.Error:
                db.rollback()
                mensagem = "Não foi possível registrar os votos. Tente novamente."

    _, enquetes = carregar_enquetes(db)
    return render_template(
        "index.html",
        enquetes=enquetes,
        mensagem=mensagem,
        mostrar_resultados=mostrar_resultados,
    )


inicializar_banco()

if __name__ == "__main__":
    app.run(
        host=os.getenv("MUSICAS_HOST", "0.0.0.0"),
        port=int(os.getenv("MUSICAS_PORT", "4444")),
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"},
    )
