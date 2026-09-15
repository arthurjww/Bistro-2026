from ..banco_de_dados import get_db

def obter_alunos_filtro():
    db = get_db()

    cursor = db.execute(
        '''SELECT cod_aluno,
                  nome_aluno AS nome
           FROM Aluno
           ORDER BY nome_aluno;
        '''
    )

    resultado = cursor.fetchall()

    return resultado

def obter_participantes_filtro(codigo_aluno=None):
    db = get_db()

    if codigo_aluno:
        cursor = db.execute(
            '''SELECT id,
                      nome
               FROM Ingresso
               WHERE cod_aluno = ?
               ORDER BY nome;
            ''',
            (codigo_aluno,)
            
        )
    else:
        cursor = db.execute(
            '''SELECT id,
                    nome
               FROM Ingresso
               ORDER BY nome;
            '''
        )

    resultado = cursor.fetchall()

    return resultado

def obter_detalhes_participante(numero_ingresso):
    db = get_db()

    cursor = db.execute(
        '''SELECT a.nome_aluno AS nome_aluno,
                  (
                    SELECT COUNT(i2.id)
                    FROM Ingresso AS i2
                    WHERE i2.cod_aluno = i.cod_aluno
                  ) AS qtd_ingressos,
                  i.id AS n_ingresso,
                  i.nome AS nome_cliente,
                  i.telefone AS telefone_comprador,
                  i.observacoes AS restricoes_texto,
                  strftime('%d/%m/%Y %H:%M', i.data_compra) AS data_hora_compra,
                  CASE
                    WHEN i.foi_pago = 1 THEN 'Pago'
                    ELSE 'Não pago'
                  END AS status_compra
           FROM Ingresso AS i
           INNER JOIN Aluno AS a
                  ON i.cod_aluno = a.cod_aluno
           WHERE i.id = ?
        ''',
        (numero_ingresso,)
    )

    resultado = cursor.fetchone()

    return resultado