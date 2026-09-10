from ..banco_de_dados import get_db

def obter_lista_financeiro():
    # Pega a conexão com o banco de dados.
    db = get_db()

    # Executa a consulta que reúne as informações necessárias
    # para montar o relatório financeiro.
    cursor = db.execute(
        '''SELECT
            a.nome_aluno AS aluno,

            # Conta quantos ingressos o aluno possui.
            COUNT(i.id) OVER (
                PARTITION BY i.cod_aluno
            ) AS quantidade_ingressos,

            # Número do ingresso.
            i.id AS numero_ingresso,

            # Nome informado na compra.
            i.nome AS nome_comprador,

            # O banco não possui CPF, então deixamos esse campo vazio.
            '' AS cpf,

            # Telefone informado na compra.
            i.telefone AS telefone,

            # Observações podem conter informações/restrições da compra.
            i.observacoes AS restricoes,

            # Data e horário em que o ingresso foi comprado.
            i.data_compra AS horario_e_dia_compra,

            # Converte o valor booleano em texto para o HTML.
            CASE
                WHEN i.foi_pago = 1 THEN 'Pago'
                ELSE 'Não pago'
            END AS status,

            # Valor pago pelo ingresso.
            i.valor_pago AS valor_pago

        FROM Ingresso AS i

        # Relaciona o ingresso ao aluno responsável.
        INNER JOIN Aluno AS a
            ON i.cod_aluno = a.cod_aluno

        ORDER BY
            a.nome_aluno,
            i.data_compra,
            i.id;
        '''
    )

    # Pega todas as linhas retornadas pela consulta.
    resultado = cursor.fetchall()

    # Retorna os dados para serem utilizados pelo relatório.
    return resultado
