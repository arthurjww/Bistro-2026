from ..banco_de_dados import get_db
from .cursos import obter_curso_por_nome

def obter_resumo_participantes():
    db = get_db()

    cursor = db.execute(
        '''SELECT i.cod_aluno,
                  a.nome_aluno AS aluno,
                  i.nome AS comprador,
                  i.valor_pago,
                  strftime('%d/%m/%Y %H:%M', i.data_compra) AS data_compra,
                  CASE
                      WHEN i.observacoes IS NOT NULL
                          AND TRIM(i.observacoes) != ''
                      THEN 'Sim'
                      ELSE 'Não'
                  END AS restricao,
                  SUBSTR(r.cod_lugar, 1, 1) AS n_mesa
           FROM Ingresso AS i
           INNER JOIN Aluno AS a
                  ON i.cod_aluno = a.cod_aluno
           INNER JOIN Reserva AS r
                  ON i.cod_reserva = r.cod_reserva
           WHERE i.foi_pago = 1
           ORDER BY
                  a.nome_aluno,
                  i.nome;
        '''
    )

    linhas = cursor.fetchall()
    resultado = []

    for linha in linhas:
        participante = dict(linha)

        participante["tecnico"] = (obter_curso_por_nome(participante["aluno"]) or "Não identificado")

        resultado.append(participante)

    return resultado