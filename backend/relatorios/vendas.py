from ..banco_de_dados import get_db

def obter_total_ingressos():
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(id) AS quantidade_total
           FROM Ingresso;'''
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_total']

    return quantidade

def obter_ingressos_pagos():
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(id) as quantidade_paga
           FROM Ingresso
           WHERE foi_pago=1;'''
    )

    resultado = cursor.fetchone()
    quantidade = resultado['quantidade_paga']

    return quantidade

def obter_ingressos_nao_pagos():
    db = get_db()

    cursor = db.execute(
        '''SELECT COUNT(id) as quantidade_nao_paga
           FROM Ingresso
           WHERE foi_pago=0
           or foi_pago IS NULL;'''
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