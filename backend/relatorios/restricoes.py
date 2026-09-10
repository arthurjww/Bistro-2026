from ..banco_de_dados import get_db
# Importa a função get_db do módulo banco_de_dados.
# Essa função é responsável por obter uma conexão com o banco de dados.

def obter_lista_restricoes():
# Define uma função chamada obter_lista_restricoes.
# Essa função será usada para buscar no banco todas as pessoas
# que possuem alguma restrição alimentar.

    db = get_db()
# Chama a função get_db() para abrir/obter uma conexão com o banco de dados.

    cursor = db.execute(
# Executa um comando SQL no banco de dados. O resultado da consulta será armazenado na variável cursor.

        '''SELECT
            nome_cliente AS participante,
            codigo_ingresso AS ingresso,
            numero_mesa AS mesa_lugar,
            descricao_restricao AS restricao
        FROM tabela_reservas
        WHERE descricao_restricao IS NOT NULL
          AND descricao_restricao != ''
        ORDER BY
            numero_mesa,
            codigo_ingresso;
        '''
    )

    resultado = cursor.fetchall()
# fetchall() pega todas as linhas retornadas pela consulta SQL. O resultado fica armazenado na variável resultado.

    return resultado
# Retorna todos os registros encontrados.
# Essa informação poderá ser usada pelo restante do sistema para mostrar a tabela de restrições no index.html.