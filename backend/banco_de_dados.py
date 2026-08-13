import sqlite3
from flask import g
from . import app


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
            cod_aluno CHAR(6) PRIMARY KEY,
            nome_aluno VARCHAR(50),
            usos_restantes INT DEFAULT = 2,
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ingresso (
            id INT PRIMARY KEY,
            nome VARCHAR(30),
            eh_crianca BOOL,
            observacoes VARCHAR(255),
            email_envio VARCHAR(50),
            foi_pago BOOL,
            cronometro_vaga DATETIME,
            token_QR CHAR(6) UNIQUE,
            utilizado BOOL,
            data_utilizado DATETIME,
            cod_aluno CHAR(6),
            cod_lugar VARCHAR(3),
            FOREIGN KEY (cod_aluno) REFERENCES Aluno(cod_aluno),
            FOREIGN KEY (cod_lugar) REFERENCES Lugares(cod_lugar)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Administradores (
            cod_admin INT PRIMARY KEY AUTOINCREMENT,
            nome_admin VARCHAR(50),
            senha VARCHAR(50),
            email VARCHAR(225)
            cod_aluno CHAR(6),
            FOREIGN KEY (cod_aluno) REFERENCES Aluno(cod_aluno)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Lugares (
            cod_lugar VARCHAR(3) PRIMARY KEY,
            cod_aluno VARCHAR(50),
            mesa CHAR(1),
            ocupado BOOL
        )
    ''')