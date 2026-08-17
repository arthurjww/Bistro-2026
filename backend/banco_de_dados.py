import sqlite3
from flask import g
from . import app

# método para coinseguir o db
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def create_all():
    cursor = get_db().cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Aluno (
            cod_aluno TEXT PRIMARY KEY CHECK(length(cod_aluno) = 6),
            nome_aluno TEXT NOT NULL CHECK(length(nome_aluno) <= 50)
            usos_restantes INT DEFAULT = 2,
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ingresso (
            id INT PRIMARY KEY,
            nome TEXT NOT NULL CHECK(length(nome) <= 50),
            eh_crianca BOOL,
            observacoes TEXT CHECK(length(observacoes) <= 255),
            email_envio TEXT NOT NULL CHECK(length(email_envio) <= 50),
            foi_pago BOOL,
            token_QR TEXT UNIQUE CHECK(length(token_QR) = 6),
            utilizado BOOL,
            data_utilizado DATETIME,
            cod_aluno TEXT NOT NULL CHECK(lenght(cod_aluno) = 6),
            cod_lugar TEXT NOT NULL(length(cod_lugar) <= 3),
            data_compra DATETIME,
            telefone TEXT CHECK(length(telefone) <= 20),
            FOREIGN KEY (cod_aluno) REFERENCES Aluno(cod_aluno),
            FOREIGN KEY (cod_lugar) REFERENCES Lugares(cod_lugar)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Administradores (
            cod_admin INT PRIMARY KEY AUTOINCREMENT,
            nome_admin TEXT NOT NULL CHECK(length(nome_admin) <= 50),
            senha TEXT NOT NULL(length(senha) <= 50),
            email TEXT NOT NULL CHECK(length(email) <= 255)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Lugares (
            cod_lugar TEXT PRIMARY KEY CHECK(lenght(cod_lugar) <= 3),
            cod_aluno TEXT NOT NULL CHECK(length(cod_aluno) = 6),
            mesa TEXT NOT NUUL CHECK (lengh(mesa) = 1),
            ocupado BOOL,
            cronometro_reservado DATETIME
        )
    ''')

