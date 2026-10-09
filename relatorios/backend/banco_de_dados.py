import sqlite3
from pathlib import Path
from flask import g, current_app


def _configurar_conexao(db: sqlite3.Connection) -> sqlite3.Connection:
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 30000")
    return db


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        caminho = Path(current_app.config["DATABASE"])
        caminho.parent.mkdir(parents=True, exist_ok=True)
        db = g._database = _configurar_conexao(
            sqlite3.connect(caminho, timeout=30)
        )
    return db


def close_connection(exception=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def _colunas(db, tabela):
    return {linha["name"] for linha in db.execute(f"PRAGMA table_info({tabela})").fetchall()}


def _migrar_config(db):
    existe = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Config'"
    ).fetchone()

    if existe:
        colunas = _colunas(db, "Config")
        if not {"data_dia_1", "data_dia_2"}.issubset(colunas):
            # Migra a estrutura antiga (qtd_dias/id limitado a 1) para a usada pelo sistema atual.
            db.execute("ALTER TABLE Config RENAME TO Config_antiga")
            db.execute(
                """
                CREATE TABLE Config (
                    id INTEGER NOT NULL PRIMARY KEY,
                    data_dia_1 DATETIME,
                    data_dia_2 DATETIME
                )
                """
            )
            db.execute("DROP TABLE Config_antiga")
    else:
        db.execute(
            """
            CREATE TABLE Config (
                id INTEGER NOT NULL PRIMARY KEY,
                data_dia_1 DATETIME,
                data_dia_2 DATETIME
            )
            """
        )

    db.execute(
        """
        INSERT OR IGNORE INTO Config(id, data_dia_1, data_dia_2)
        VALUES (1, '2026-10-29', '2026-10-29')
        """
    )
    db.execute(
        """
        INSERT OR IGNORE INTO Config(id, data_dia_1, data_dia_2)
        VALUES (2, '2026-10-29', '2026-10-30')
        """
    )


def _migrar_administradores(db):
    existe = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='Administradores'"
    ).fetchone()

    if not existe:
        db.execute(
            """
            CREATE TABLE Administradores(
                cod_admin INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_admin TEXT NOT NULL CHECK(length(nome_admin) <= 50),
                senha TEXT NOT NULL CHECK(length(senha) <= 255),
                email TEXT NOT NULL CHECK(length(email) <= 255)
            )
            """
        )
        return

    sql = (existe["sql"] or "").lower().replace(" ", "")
    # Bancos antigos limitavam o hash da senha a 50 caracteres. Werkzeug usa hashes maiores.
    if "length(senha)<=50" in sql:
        db.execute("ALTER TABLE Administradores RENAME TO Administradores_antiga")
        db.execute(
            """
            CREATE TABLE Administradores(
                cod_admin INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_admin TEXT NOT NULL CHECK(length(nome_admin) <= 50),
                senha TEXT NOT NULL CHECK(length(senha) <= 255),
                email TEXT NOT NULL CHECK(length(email) <= 255)
            )
            """
        )
        db.execute(
            """
            INSERT INTO Administradores(cod_admin, nome_admin, senha, email)
            SELECT cod_admin, nome_admin, senha, email
            FROM Administradores_antiga
            """
        )
        db.execute("DROP TABLE Administradores_antiga")


def create_all():
    """Cria/migra a estrutura sem apagar dados existentes."""
    db = get_db()

    # WAL melhora a convivência entre os três processos usando o mesmo SQLite.
    try:
        db.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Aluno (
            cod_aluno TEXT PRIMARY KEY CHECK(length(cod_aluno) = 6),
            nome_aluno TEXT NOT NULL CHECK(length(nome_aluno) <= 50),
            usos_restantes INTEGER NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Lugares(
            cod_lugar TEXT PRIMARY KEY CHECK(length(cod_lugar) <= 3),
            salao INTEGER NOT NULL CHECK(salao IN (1, 2))
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Reserva(
            cod_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_lugar TEXT NOT NULL,
            cod_aluno TEXT NOT NULL,
            dia_bistro TEXT NOT NULL,
            ocupado INTEGER NOT NULL DEFAULT 0 CHECK(ocupado IN(0,1,2)),
            cronometro_reservado INTEGER,
            UNIQUE(cod_lugar, dia_bistro),
            FOREIGN KEY (cod_lugar) REFERENCES Lugares(cod_lugar),
            FOREIGN KEY (cod_aluno) REFERENCES Aluno(cod_aluno)
        )
        """
    )

    _migrar_administradores(db)

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Ingresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL CHECK(length(nome) <= 50),
            tipo_ingresso INTEGER NOT NULL CHECK(tipo_ingresso IN (0, 1, 2)),
            observacoes TEXT CHECK(length(observacoes) <= 255),
            email_envio TEXT NOT NULL CHECK(length(email_envio) <= 50),
            foi_pago INTEGER NOT NULL DEFAULT 0 CHECK(foi_pago IN (0, 1)),
            token_QR TEXT UNIQUE CHECK(length(token_QR) = 6),
            utilizado INTEGER NOT NULL DEFAULT 0 CHECK(utilizado IN (0, 1)),
            data_utilizado DATETIME,
            cod_aluno TEXT NOT NULL CHECK(length(cod_aluno) = 6),
            cod_reserva INTEGER,
            data_compra DATETIME,
            telefone TEXT NOT NULL CHECK(length(telefone) <= 11),
            valor_pago REAL NOT NULL CHECK(valor_pago >= 0),
            FOREIGN KEY (cod_aluno) REFERENCES Aluno(cod_aluno),
            FOREIGN KEY (cod_reserva) REFERENCES Reserva(cod_reserva)
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS Pedido (
            referencia_externa TEXT PRIMARY KEY,
            order_id TEXT,
            tokens TEXT NOT NULL,
            cod_aluno TEXT,
            valor REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            criado_em TIMESTAMP NOT NULL
        )
        """
    )

    # A votação grava nesta mesma tabela que o painel de relatórios consulta.
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

    _migrar_config(db)

    db.execute("CREATE INDEX IF NOT EXISTS idx_ingresso_pago ON Ingresso(foi_pago)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ingresso_aluno ON Ingresso(cod_aluno)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_reserva_dia ON Reserva(dia_bistro)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_musicas_votos ON musicas(votos DESC)")
    db.commit()
