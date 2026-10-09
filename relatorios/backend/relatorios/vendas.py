from ..banco_de_dados import get_db

def obter_total_ingressos(dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(i.id) AS quantidade_total
           FROM Ingresso AS i
           INNER JOIN Reserva AS r
                   ON i.cod_reserva = r.cod_reserva
           WHERE (? IS NULL OR r.dia_bistro = ?);
        ''',
        (dia_bistro, dia_bistro)
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_total']

    return quantidade

def obter_ingressos_pagos(dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(i.id) AS quantidade_paga
           FROM Ingresso AS i
           INNER JOIN Reserva AS r
                   ON i.cod_reserva = r.cod_reserva
           WHERE i.foi_pago = 1
             AND (? IS NULL OR r.dia_bistro = ?);
        ''',
        (dia_bistro, dia_bistro)
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_paga']

    return quantidade

def obter_ingressos_nao_pagos(dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(i.id) AS quantidade_nao_paga
           FROM Ingresso AS i
           INNER JOIN Reserva AS r
                   ON i.cod_reserva = r.cod_reserva
           WHERE (
               i.foi_pago = 0
               OR i.foi_pago IS NULL
           )
             AND (? IS NULL OR r.dia_bistro = ?);
        ''',
        (dia_bistro, dia_bistro)
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_nao_paga']

    return quantidade

def obter_ingressos_restantes():
    db = get_db()

    cursor = db.execute(
        '''SELECT COALESCE(SUM(usos_restantes), 0) AS quantidade_restante
           FROM Aluno;
        '''
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_restante']

    return quantidade

def obter_ingressos_restantes_por_aluno():
    db = get_db()

    cursor = db.execute(
        '''SELECT cod_aluno,
                  nome_aluno,
                  usos_restantes
           FROM Aluno
           WHERE usos_restantes > 0
           ORDER BY usos_restantes DESC, nome_aluno;
        '''
    )

    resultado = cursor.fetchall()

    return resultado

def obter_lista_vendas(dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT
            a.nome_aluno,
            COUNT(i.id) OVER (
                PARTITION BY i.cod_aluno
            ) AS quant_por_aluno,
            i.id AS numero_ingresso,
            'Lugar ' || r.cod_lugar || ' / Salão ' || l.salao AS lugar_e_mesa,
            strftime('%d/%m/%Y', r.dia_bistro) AS dia_bistro,
            CASE
                WHEN i.foi_pago = 1 THEN 'Pago'
                ELSE 'Não pago'
            END AS situacao_pagamento
        FROM Ingresso AS i
        INNER JOIN Aluno AS a
            ON i.cod_aluno = a.cod_aluno
        INNER JOIN Reserva AS r
            ON i.cod_reserva = r.cod_reserva
        INNER JOIN Lugares AS l
            ON r.cod_lugar = l.cod_lugar
        WHERE (? IS NULL OR r.dia_bistro = ?)
        ORDER BY
            r.dia_bistro,
            a.nome_aluno,
            l.salao,
            r.cod_lugar;
        ''',
        (dia_bistro, dia_bistro)
    )

    resultado = cursor.fetchall()

    return resultado
