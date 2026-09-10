from ..banco_de_dados import get_db

def obter_lista_financeiro():
    db = get_db()

    cursor = db.execute(
        '''SELECT a.nome_aluno AS aluno,
                  COUNT(i.id) OVER (
                  PARTITION BY i.cod_aluno
                  ) AS quantidade_ingressos,
                  i.id AS numero_ingresso,
                  i.nome AS nome_comprador,
                  i.telefone,
                  i.observacoes AS restricoes,
                  strftime('%d/%m/%Y %H:%M', i.data_compra) AS horario_e_dia_compra,
                  i.valor_pago,
                  'Pago' AS status
           FROM Ingresso AS i
           INNER JOIN Aluno AS a
                  ON i.cod_aluno=a.cod_aluno
           WHERE i.foi_pago = 1
           ORDER BY i.data_compra DESC;
        '''
    )

    resultado = cursor.fetchall()

    return resultado
