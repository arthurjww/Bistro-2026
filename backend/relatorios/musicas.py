from ..banco_de_dados import get_db


def obter_top_5_musicas():
    db = get_db()

    tabela_existe = db.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND LOWER(name) = 'musicas';
        """
    ).fetchone()

    if tabela_existe is None:
        return []

    colunas = {
        coluna["name"]
        for coluna in db.execute(
            "PRAGMA table_info(musicas);"
        ).fetchall()
    }

    colunas_necessarias = {"num", "nome", "artista", "votos"}

    if not colunas_necessarias.issubset(colunas):
        return []

    cursor = db.execute(
        """
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    COALESCE(votos, 0) DESC,
                    nome COLLATE NOCASE,
                    num
            ) AS posicao,
            nome AS titulo,
            artista,
            COALESCE(votos, 0) AS votos
        FROM musicas
        ORDER BY
            COALESCE(votos, 0) DESC,
            nome COLLATE NOCASE,
            num
        LIMIT 5;
        """
    )

    return cursor.fetchall()
