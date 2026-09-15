from backend.banco_de_dados import get_db

LIVRE = 0
OCUPADO = 1
EM_PAGAMENTO = 2

STATUS_VALIDOS = (LIVRE, OCUPADO, EM_PAGAMENTO)

LAYOUT_MESAS_GALPAO1 = {
    "A": 8, "B": 6, "C": 8, "D": 8, "E": 8, "F": 8, "G": 8,
    "H": 6, "I": 6, "J": 6, "K": 6
}

LAYOUT_MESAS_GALPAO2 = {
    "L":6, "M":6, "N":6,
    "O":6, "P":8
}


class LugarInvalidoError(Exception):
    pass

class LugarIndisponivelError(Exception):
    pass

class Salao():
    LAYOUT = {}
    NUMERO_SALAO = None  

    def validar_cod_lugar(self, cod_lugar):
        if not cod_lugar or len(cod_lugar) < 1 or len(cod_lugar) > 2:
            raise LugarInvalidoError(f'Código de lugar errado: {cod_lugar}')

        mesa = cod_lugar[0].upper()
        try:
            cadeira = int(cod_lugar[1:])
        except ValueError:
            raise LugarInvalidoError(f"Número de cadeira inválido em: {cod_lugar}")

        if mesa not in self.LAYOUT:
            raise LugarInvalidoError(f'Mesa {mesa} não existe')

        if cadeira < 1 or cadeira > self.LAYOUT[mesa]:
            raise LugarInvalidoError(
                f'{mesa} não possui a cadeira {cadeira}. '
                f'Lugares disponiveis: {self.LAYOUT[mesa]}'
            )

        return mesa, cadeira

    def seed_lugares(self):
        if self.NUMERO_SALAO is None:
            raise NotImplementedError("Defina NUMERO_SALAO na subclasse antes de usar seed_lugares()")

        db = get_db()
        cursor = db.cursor()

        for mesa, qtd_cadeiras in self.LAYOUT.items():
            for cadeira in range(1, qtd_cadeiras + 1):
                cod_lugar = f"{mesa}{cadeira}"
                cursor.execute("""
                    INSERT OR IGNORE INTO Lugares (cod_lugar, salao) VALUES (?, ?)
                """, (cod_lugar, self.NUMERO_SALAO))
        db.commit()

    # Recebe dia_bistro e usa LEFT_JOIN com Reserva
    # Se não existe reserva para aquele lugar+dia, considera livre (ocupado=0)
    def listar_mapa(self, dia_bistro):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT L.cod_lugar, 
               COALESCE(R.ocupado, 0) AS ocupado
            FROM Lugares AS L
            LEFT JOIN Reservas AS R
                ON R.cod_lugar = L.cod_lugar
                AND R.dia_bistro = ?
            WHERE L.salao = ?
            ORDER BY L.cod_lugar
        """), (dia_bistro, self.NUMERO_SALAO)

        mapa = {}
        for linha in cursor.fetchall():
            cod_lugar = linha["cod_lugar"]
            mesa = cod_lugar[0]
            cadeira = int(cod_lugar[1:])
            mapa.setdefault(linha["mesa"], []).append({
                "cod_lugar": cod_lugar,
                "cadeira": cadeira,
                "ocupado": linha["ocupado"]
            })
        return mapa

    # Escolher lugar agora, obrigatoriamente precisa saber o dia da reserva
    def escolher_lugar(self, cod_lugar, cod_aluno, dia_bistro):
        self.validar_cod_lugar(cod_lugar)
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO Reserva (cod_lugar, cod_aluno, dia_bistro, ocupado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cod_lugar, dia_bistro) DO UPDATE SET
                cod_aluno = excluded.cod_aluno,
                ocupado = excluded.ocupado
            WHERE Reserva.ocupado = 0
        """, (cod_lugar, cod_aluno, dia_bistro, LIVRE))

        db.commit()

        if cursor.rowcount == 0:
            return False, "Lugar indisponível"

        linha = db.execute("""
            SELECT cod_reserva
            FROM reserva
            WHERE cod_lugar = ? 
            AND dia_bistro = ?
        """, (cod_lugar, dia_bistro)).fetchone()

        return True, linha["cod_reserva"]
    
class Salao1(Salao):
    LAYOUT = LAYOUT_MESAS_GALPAO1
    NUMERO_SALAO = 1 


class Salao2(Salao):
    LAYOUT = LAYOUT_MESAS_GALPAO2
    NUMERO_SALAO = 2

def qual_salao(cod_lugar):
    if not cod_lugar:
        raise LugarInvalidoError(f'Código de lugar errado: {cod_lugar}')

    mesa = cod_lugar[0].upper()

    if mesa in LAYOUT_MESAS_GALPAO1:
        return Salao1
    if mesa in LAYOUT_MESAS_GALPAO2:
        return Salao2
    if mesa not in LAYOUT_MESAS_GALPAO1 or mesa not in LAYOUT_MESAS_GALPAO2:
        raise LugarInvalidoError(f'Mesa {mesa} não existe')


def obter_qtd_dias():
    db = get_db()
    linha = db.execute('SELECT qtd_dias FROM Config WHERE id = 1').fetchone()

    if not linha:
        return 1

    return linha['qtd_dias']

def salao2_esta_oculto():
    return obter_qtd_dias() == 2

def listar_saloes_disponiveis():
    if salao2_esta_oculto():
        return [Salao1]
    else:
        return [Salao1, Salao2]
