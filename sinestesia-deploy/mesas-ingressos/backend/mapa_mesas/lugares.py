from backend.banco_de_dados import get_db

LIVRE = 0
OCUPADO = 1
EM_PAGAMENTO = 2

LAYOUT_MESAS = {
    letra: 6 for letra in "ABCDEFGHIJKLMN"
}

class LugarInvalidoError(Exception):
    pass

class LugarIndisponivelError(Exception):
    pass

class MapaLugares:
    def validar_cod_lugar(self, cod_lugar):
        if not cod_lugar or len(cod_lugar) != 2:
            raise LugarInvalidoError(f"Codigo de lugar errado: {cod_lugar}")

        cod_lugar = cod_lugar.upper()
        mesa = cod_lugar[0]

        try:
            cadeira = int(cod_lugar[1:])
        except ValueError:
            raise LugarInvalidoError(
                f"Numero de cadeira invalido em: {cod_lugar}"
            )

        if mesa not in LAYOUT_MESAS or cadeira < 1 or cadeira > 6:
            raise LugarInvalidoError(f"Lugar inexistente: {cod_lugar}")

        return cod_lugar

    def codigos_validos(self):
        return [
            f"{mesa}{cadeira}"
            for mesa in LAYOUT_MESAS
            for cadeira in range(1, 7)
        ]

    def seed_lugares(self):
        db = get_db()
        codigos = [(codigo,) for codigo in self.codigos_validos()]

        db.executemany(
            "INSERT OR IGNORE INTO Lugares (cod_lugar, salao) VALUES (?, 1)",
            codigos
        )
        db.commit()

    def listar_mapa(self, dia_bistro):
        db = get_db()
        codigos = self.codigos_validos()
        placeholders = ",".join("?" for _ in codigos)

        linhas = db.execute(
            f"""
            SELECT L.cod_lugar,
                CASE
                    WHEN substr(L.cod_lugar, 1, 1) = 'H' THEN 1
                    ELSE COALESCE(R.ocupado, 0)
                END AS ocupado
            FROM Lugares AS L
            LEFT JOIN Reserva AS R
                ON R.cod_lugar = L.cod_lugar
                AND R.dia_bistro = ?
            WHERE L.cod_lugar IN ({placeholders})
            ORDER BY L.cod_lugar
            """,
            (dia_bistro, *codigos)
        ).fetchall()

        mapa = {}
        for linha in linhas:
            codigo = linha["cod_lugar"]
            mapa.setdefault(codigo[0], []).append({
                "cod_lugar": codigo,
                "cadeira": int(codigo[1:]),
                "ocupado": linha["ocupado"]
            })

        return mapa

    def escolher_lugar(self, cod_lugar, cod_aluno, dia_bistro):
        cod_lugar = self.validar_cod_lugar(cod_lugar)
        if cod_lugar.startswith("H"):
            return False, "Mesa H indisponível"
        db = get_db()

        cursor = db.execute(
            """
            INSERT INTO Reserva (cod_lugar, cod_aluno, dia_bistro, ocupado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cod_lugar, dia_bistro) DO UPDATE SET
                cod_aluno = excluded.cod_aluno,
                ocupado = excluded.ocupado
            WHERE Reserva.ocupado = 0
            """,
            (cod_lugar, cod_aluno, dia_bistro, EM_PAGAMENTO)
        )
        db.commit()

        if cursor.rowcount == 0:
            return False, "Lugar indisponivel"

        reserva = db.execute(
            """
            SELECT cod_reserva
            FROM Reserva
            WHERE cod_lugar = ?
              AND cod_aluno = ?
              AND dia_bistro = ?
            """,
            (cod_lugar, cod_aluno, dia_bistro)
        ).fetchone()

        return True, reserva["cod_reserva"]