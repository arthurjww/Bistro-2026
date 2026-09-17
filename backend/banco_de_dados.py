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

            usos_restantes INTEGER NOT NULL
        )
    """)

    # lugares
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS Lugares(
           cod_lugar TEXT PRIMARY KEY
               CHECK (length(cod_lugar) <= 3),
    
           salao INTEGER NOT NULL
               CHECK (salao IN (1, 2))
       )
   """)

    # reserva
    # ocupado 0 = livre 1 = ocupado 2 = em pagamento / reservado
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS Reserva(
           cod_reserva          INTEGER PRIMARY KEY AUTOINCREMENT,

           cod_lugar            TEXT    NOT NULL,
           
           cod_aluno            TEXT    NOT NULL,
            
            dia_bistro TEXT NOT NULL,
            
            ocupado INTEGER NOT NULL DEFAULT 0
                CHECK(ocupado IN(0,1,2)),
            
            cronometro_reservado INTEGER,
            
            UNIQUE(cod_lugar, dia_bistro),

            FOREIGN KEY (cod_lugar)
                REFERENCES Lugares(cod_lugar),
        
            FOREIGN KEY (cod_aluno)
                REFERENCES Aluno(cod_aluno)
       )
   """)

    #admin 
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS Administradores(
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

            tipo_ingresso INTEGER NOT NULL
                CHECK(tipo_ingresso IN (0, 1, 2)),

            observacoes TEXT 
                CHECK(length(observacoes) <= 255),
            
            email_envio TEXT NOT NULL
                CHECK(length(email_envio) <= 50),

            foi_pago INTEGER NOT NULL DEFAULT 0
                CHECK(foi_pago IN (0, 1)),

            token_QR TEXT UNIQUE
                CHECK(length(token_QR) = 6),

            utilizado INTEGER NOT NULL DEFAULT 0
                CHECK(utilizado IN (0, 1)),

            data_utilizado DATETIME,

            cod_aluno TEXT NOT NULL
                CHECK(length(cod_aluno) = 6),

            cod_reserva INTEGER,

            data_compra DATETIME,

            telefone TEXT NOT NULL
                CHECK(length(telefone) <= 11),
                
             valor_pago REAL NOT NULL
                CHECK (valor_pago >= 0), 

            FOREIGN KEY (cod_aluno)
                REFERENCES Aluno(cod_aluno),

            FOREIGN KEY (cod_reserva)
                REFERENCES Reserva(cod_reserva)
        )
    """)

    db.execute('''
        CREATE TABLE IF NOT EXISTS Pedido (
            referencia_externa TEXT PRIMARY KEY,
            order_id TEXT,
            tokens TEXT NOT NULL,
            cod_aluno TEXT,
            valor REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            criado_em TIMESTAMP NOT NULL
        )
    ''')

    # quantidade de dias
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS Config
       (
           id       INTEGER NOT NULL PRIMARY KEY,
           data_dia_1 DATETIME,
           data_dia_2 DATETIME
       )
   """)

    cursor.execute("""
        INSERT OR IGNORE INTO Config(id, data_dia_1, data_dia_2)
        VALUES (1,'2026-10-29','2026-10-29')""")

    cursor.execute("""
        INSERT OR IGNORE INTO Config (id, data_dia_1, data_dia_2)
        VALUES (2,'2026-10-29','2026-10-30')""")

    #commit - salva aterações 
    db.commit()


