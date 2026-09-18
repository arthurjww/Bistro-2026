from ..banco_de_dados import get_db
from .cursos import obter_curso_por_nome

def pertence_ao_curso(nome_aluno, curso_tecnico):
    if not curso_tecnico or curso_tecnico == "todos":
        return True

    return obter_curso_por_nome(nome_aluno) == curso_tecnico

def obter_alunos_filtro(curso_tecnico=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT cod_aluno,
                  nome_aluno AS nome
           FROM Aluno
           ORDER BY nome_aluno;
        '''
    )

    linhas = cursor.fetchall()
    resultado = []

    for linha in linhas:
        aluno = dict(linha)

        if pertence_ao_curso(aluno["nome"], curso_tecnico):
            resultado.append(aluno)

    return resultado

def obter_participantes_filtro(codigo_aluno=None, curso_tecnico=None,
                               dia_bistro=None):
    db = get_db()

    if codigo_aluno:
        cursor = db.execute(
            """
            SELECT
                i.id,
                i.nome,
                a.nome_aluno
            FROM Ingresso AS i
            INNER JOIN Aluno AS a
                ON i.cod_aluno = a.cod_aluno
            INNER JOIN Reserva AS r
                ON i.cod_reserva = r.cod_reserva
            WHERE i.cod_aluno = ?
              AND (? IS NULL OR r.dia_bistro = ?)
            ORDER BY i.nome;
            """,
            (codigo_aluno, dia_bistro, dia_bistro)
        )
    else:
        cursor = db.execute(
            """
            SELECT
                i.id,
                i.nome,
                a.nome_aluno
            FROM Ingresso AS i
            INNER JOIN Aluno AS a
                ON i.cod_aluno = a.cod_aluno
            INNER JOIN Reserva AS r
                ON i.cod_reserva = r.cod_reserva
            WHERE (? IS NULL OR r.dia_bistro = ?)
            ORDER BY i.nome;
            """,
            (dia_bistro, dia_bistro)
        )

    linhas = cursor.fetchall()
    resultado = []

    for linha in linhas:
        participante = dict(linha)

        if pertence_ao_curso(
            participante["nome_aluno"],
            curso_tecnico
        ):
            resultado.append({
                "id": participante["id"],
                "nome": participante["nome"]
            })

    return resultado

def obter_detalhes_participante(numero_ingresso, dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT a.nome_aluno AS nome_aluno,
                  (
                    SELECT COUNT(i2.id)
                    FROM Ingresso AS i2
                    INNER JOIN Reserva AS r2
                            ON i2.cod_reserva = r2.cod_reserva
                    WHERE i2.cod_aluno = i.cod_aluno
                      AND (? IS NULL OR r2.dia_bistro = ?)
                  ) AS qtd_ingressos,
                  i.id AS n_ingresso,
                  i.nome AS nome_cliente,
                  i.telefone AS telefone_comprador,
                  i.observacoes AS restricoes_texto,
                  strftime('%d/%m/%Y %H:%M', i.data_compra) AS data_hora_compra,
                  strftime('%d/%m/%Y', r.dia_bistro) AS dia_bistro,
                  CASE
                    WHEN i.foi_pago = 1 THEN 'Pago'
                    ELSE 'Não pago'
                  END AS status_compra
           FROM Ingresso AS i
           INNER JOIN Aluno AS a
                  ON i.cod_aluno = a.cod_aluno
           INNER JOIN Reserva AS r
                  ON i.cod_reserva = r.cod_reserva
           WHERE i.id = ?
             AND (? IS NULL OR r.dia_bistro = ?)
        ''',
        (dia_bistro, dia_bistro, numero_ingresso, dia_bistro, dia_bistro)
    )

    resultado = cursor.fetchone()

    return resultado
