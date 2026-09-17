from ..banco_de_dados import get_db
def obter_top_5_musicas():
    db=get_db()

    cursor=db.execute(
        '''
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    COALESCE(votos,0) DESC,
                    nome COLLATE NOCASE,
                    num
            ) AS posicao,
            nome AS titulo,
            artista,
            COALESCE(votos,0) AS votos
        FROM musicas
        ORDER BY
            COALESCE(votos,0) DESC,
            nome COLLATE NOCASE,
            num
        LIMIT 5;
        '''
    )
    resultado=cursor.fetchall()

    return resultado
