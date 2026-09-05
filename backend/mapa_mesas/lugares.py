from banco_de_dados import get_db

LIVRE = 0
OCUPADO = 1
EM_PAGAMENTO = 2

STATUS_VALIDOS = (LIVRE, OCUPADO, EM_PAGAMENTO)

LAYOUT_MESAS = {
    "A": 8, "B": 6, "C": 8, "D": 0, "E": 8, "F": 8, "G": 8,
    "H": 6, "I": 6, "J": 6, "K": 6
}

class LugarInvalidoError(Exception):
    pass

class LugarIndisponivelError(Exception):
    pass

def validar_cod_lugar(cod_lugar):
    if not cod_lugar or len(cod_lugar) < 1 or len(cod_lugar) > 2:
        raise LugarInvalidoError(f'Código de lugar errado: {cod_lugar}')

    mesa = cod_lugar[0].upper()
    try:
        cadeira = int(cod_lugar[1:])
    except ValueError:
        raise LugarInvalidoError(f"Número de cadeira inválido em: {cod_lugar}")

    if mesa not in LAYOUT_MESAS:
        raise LugarInvalidoError(f'Mesa {mesa} não existe')

    if cadeira < 1 or cadeira > LAYOUT_MESAS[mesa]:
        raise LugarInvalidoError(f'{mesa} não possui a cadeira {cadeira}. Lugares disponiveis: {LAYOUT_MESAS[mesa]}')

    return mesa, cadeira

def seed_lugares():
    db = get_db()
    cursor = db.cursor()

    for mesa, qtd_cadeiras in LAYOUT_MESAS.items():
        for cadeira in range(1, qtd_cadeiras + 1):
            cod_lugar = f"{mesa}{cadeira}"
            cursor.execute("""
                INSERT OR IGNORE INTO Lugares (cod_lugar, mesa, cadeira, ocupado) VALUES (?, ?, ?, ?)
            """, (cod_lugar, mesa, cadeira, LIVRE))
    db.commit()

def listar_mapa():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT cod_lugar, mesa, cadeira, ocupado
        FROM Lugares
        ORDER BY mesa, cadeira
    """)

    mapa = {}
    for linha in cursor.fetchall():
        mapa.setdefault(linha["mesa"], []).append({
            "cod_lugar": linha["cod_lugar"],
            "cadeira": linha["cadeira"],
            "ocupado": linha["ocupado"]
        })
    return mapa

def escolher_lugar(cod_lugar, cod_aluno):
    validar_cod_lugar(cod_lugar)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE Lugares
        SET ocupado = ?, cod_aluno = ?, cronometro_reservado = CURRENT_TIMESTAMP
        WHERE cod_lugar = ? AND ocupado = ?
    """, (EM_PAGAMENTO, cod_aluno, cod_lugar, LIVRE))

    db.commit()

    if cursor.rowcount == 0:
        return False, "Lugar indisponível"

    return True, None

def confirmar_pagamento(cod_lugar, cod_aluno):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE Lugares
        SET ocupado = ?
        WHERE cod_lugar = ? AND cod_aluno = ? AND ocupado = ?
    """, (OCUPADO, cod_lugar, cod_aluno, EM_PAGAMENTO))

    db.commit()

    if cursor.rowcount == 0:
        return False, "Reserva não encontrada ou já expirada"

    return True, None
