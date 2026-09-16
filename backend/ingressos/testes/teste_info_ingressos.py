"""
Cria 1 Aluno com cod impossível,
     2 Lugares que não existem originalmente,
     2 Reservas de cod 1 e 2

Exclui elas em toda tentativa e as recria
     Para resetar autoincrement de Reserva, passe True como arg
     na função excluir_dados_teste

Para testes:
     Depure esse arquivo
     Vá para /dummy-route, que redireciona para /info_ingressos
"""

from backend.banco_de_dados import get_db
from backend import app

from flask import session, redirect, url_for
from time import time


def criar_dados_teste():
    db = get_db()

    db.execute("""
        INSERT OR IGNORE INTO Aluno
            (cod_aluno, nome_aluno, usos_restantes)
        VALUES (?, ?, ?)
    """, ("ABCDEF", "TESTE", 2))

    db.execute("""
        INSERT OR IGNORE INTO Lugares
            (cod_lugar, salao)
        VALUES (?, ?)
    """, ("Z1", 1))

    db.execute("""
        INSERT OR IGNORE INTO Reserva
            (cod_lugar, cod_aluno, dia_bistro, ocupado, cronometro_reservado)
        VALUES (?, ?, ?, ?, ?)
    """, ("Z1", "ABCDEF", "19", 2, None))

    db.execute("""
        INSERT OR IGNORE INTO Lugares
            (cod_lugar, salao)
        VALUES (?, ?)
    """, ("Z2", 1))

    db.execute("""
        INSERT OR IGNORE INTO Reserva
            (cod_lugar, cod_aluno, dia_bistro, ocupado, cronometro_reservado)
        VALUES (?, ?, ?, ?, ?)
    """, ("Z2", "ABCDEF", "20", 2, None))

    db.commit()


def excluir_dados_teste(reset_autoincrement=False):
    db = get_db()

    cods_reservas = conseguir_reservas()

    if cods_reservas:
        placeholders = ','.join('?' for _ in cods_reservas)

        db.execute(f"""
            DELETE FROM Ingresso
            WHERE cod_reserva IN ({placeholders})
        """, cods_reservas)

    db.execute("""
        DELETE FROM Reserva
        WHERE cod_aluno = ?
          AND cod_lugar IN (?, ?)
    """, ("ABCDEF", "Z1", "Z2"))

    db.execute("""
        DELETE FROM Lugares
        WHERE cod_lugar IN (?, ?)
    """, ("Z1", "Z2"))

    db.execute("""
        DELETE FROM Aluno
        WHERE cod_aluno = ?
    """, ("ABCDEF",))

    # Resetar o AUTOINCREMENT da tabela Reserva
    if reset_autoincrement:
        db.execute("""
            DELETE FROM sqlite_sequence
            WHERE name = 'Reserva'
        """)

    db.commit()


def conseguir_reservas():
    db = get_db()

    reservas = db.execute("""
                          SELECT cod_reserva
                          FROM Reserva
                          WHERE cod_aluno = ?
                            AND cod_lugar IN (?, ?)
                          """, ("ABCDEF", "Z1", "Z2")).fetchall()

    cods_reservas = [reserva['cod_reserva'] for reserva in reservas]

    return cods_reservas


def alterar_cronometro(cods_reservas, novo_valor):
    if not cods_reservas:
        return

    db = get_db()

    placeholders = ','.join('?' for _ in cods_reservas)

    db.execute(f"""
        UPDATE Reserva
        SET cronometro_reservado = ?
        WHERE cod_reserva IN ({placeholders})
    """, (novo_valor, *cods_reservas))

    db.commit()


@app.route('/dummy-route')
def dummy_route():
    cods_reservas = conseguir_reservas()
    cod_aluno = 'ABCDEF'

    cronometro = int(time() * 1000) + 30 * 60_000

    alterar_cronometro(cods_reservas, cronometro)

    session['reservas'] = cods_reservas
    session['codigo'] = cod_aluno
    session['cronometro_reservado'] = cronometro
    session.permanent = True

    return redirect(url_for('routes.informacoes'))


if __name__ == '__main__':
    with app.app_context():
        excluir_dados_teste()
        criar_dados_teste()

    app.run(
        port=8080,
        debug=True,
        use_reloader=False
    )
