import sqlite3
from flask import g, current_app

# method para coinseguir o db
def get_db(): #retorna conexão com o banco de dados atual 

    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = sqlite3.connect(
            current_app.config["DATABASE"]
            )
        db.row_factory = sqlite3.Row
        
    return db

#fechar conexão 

#@current_app.teardown_appcontext  - linha comentada p/ ser ignorada e ver se arrumamos a conexão do banco e do init 
def close_connection(exception = None):
    #fehca a conexão do banco 
    db = getattr(g, "_database", None)

    if db is not None:
        db.close()


def create_all():
    #cria todas as tabelas caso não existam
    db = get_db()
    cursor = db.cursor()

    #aluno 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Aluno (
            cod_aluno TEXT PRIMARY KEY 
                CHECK(length(cod_aluno) = 6),

            nome_aluno TEXT NOT NULL 
                CHECK(length(nome_aluno) <= 50),

            usos_restantes INT DEFAULT  2
        )
    """)


    #lugares
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Lugares (
            cod_lugar TEXT PRIMARY KEY 
                CHECK(length(cod_lugar) <= 3),

            cod_aluno TEXT NOT NULL 
                CHECK(length(cod_aluno) = 6),

            mesa TEXT NOT NULL 
                CHECK(length(mesa) = 1),

            ocupado BOOLEAN,

            cronometro_reservado DATETIME,

            FOREIGN KEY(cod_aluno)
                REFERENCES Aluno(cod_aluno)
        )
    """)

    #admin 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Administradores (
            cod_admin INTEGER PRIMARY KEY AUTOINCREMENT,

            nome_admin TEXT NOT NULL 
                CHECK(length(nome_admin) <= 50),

            senha TEXT NOT NULL 
                CHECK(length(senha) <= 50),

            email TEXT NOT NULL 
                CHECK(length(email) <= 255)
        )
    """)


    #ingresso 
    #tipo_ingresso é 0 (de graça), 1 (meia) e 2 (inteira)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ingresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL
                CHECK(length(nome) <= 50),

            tipo_ingresso INT,

            observacoes TEXT 
                CHECK(length(observacoes) <= 255),
            
            nro_telefone TEXT NOT NULL
                CHECK(length(nro_telefone) = 11),
            
            email_envio TEXT NOT NULL
                CHECK(length(email_envio) <= 50),

            foi_pago BOOLEAN,

            token_QR TEXT UNIQUE
                CHECK(length(token_QR) = 6),

            utilizado BOOLEAN,

            data_utilizado DATETIME,

            cod_aluno TEXT NOT NULL
                CHECK(length(cod_aluno) = 6),

            cod_lugar TEXT NOT NULL
                CHECK(length(cod_lugar) <= 3),

            data_compra DATETIME,

            telefone TEXT
                CHECK(length(telefone) <= 20),
            
                
             valor_pago REAL NOT NULL
                CHECK (valor_pago >= 0), 

            FOREIGN KEY (cod_aluno)
                REFERENCES Aluno(cod_aluno),

            FOREIGN KEY (cod_lugar)
                REFERENCES Lugares(cod_lugar)
        )
    """)

    #commit - salva aterações 
    db.commit()



