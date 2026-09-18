from datetime import datetime

from ..banco_de_dados import get_db


def formatar_dia_bistro(dia):
    try:
        return datetime.fromisoformat(str(dia)).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(dia)


def obter_dias_bistro():
    db = get_db()
    dias = set()

    reservas = db.execute(
        '''SELECT DISTINCT dia_bistro
           FROM Reserva
           WHERE dia_bistro IS NOT NULL
             AND TRIM(dia_bistro) != '';
        '''
    ).fetchall()

    dias.update(reserva["dia_bistro"] for reserva in reservas)

    colunas_config = {
        coluna["name"]
        for coluna in db.execute("PRAGMA table_info(Config);").fetchall()
    }

    colunas_datas = {"data_dia_1", "data_dia_2"}

    if colunas_datas.issubset(colunas_config):
        configuracoes = db.execute(
            '''SELECT data_dia_1, data_dia_2
               FROM Config;
            '''
        ).fetchall()

        for configuracao in configuracoes:
            dias.update(
                dia for dia in (
                    configuracao["data_dia_1"],
                    configuracao["data_dia_2"]
                ) if dia
            )

    return [{"valor": dia, "texto": formatar_dia_bistro(dia)}
            for dia in sorted(dias)]


def obter_resumo_financeiro(dia_bistro=None):
    db = get_db()

    resultado = db.execute(
        '''SELECT COALESCE(SUM(i.valor_pago), 0) AS faturamento_total,
                  COUNT(i.id) AS vendas_confirmadas,
                  COALESCE(AVG(i.valor_pago), 0) AS ticket_medio
           FROM Ingresso AS i
           INNER JOIN Reserva AS r
                   ON i.cod_reserva = r.cod_reserva
           WHERE i.foi_pago = 1
             AND (? IS NULL OR r.dia_bistro = ?);
        ''',
        (dia_bistro, dia_bistro)
    ).fetchone()

    return resultado


def obter_lista_financeiro(dia_bistro=None):
    db = get_db()

    cursor = db.execute(
        '''SELECT a.nome_aluno AS aluno,
                  COUNT(i.id) OVER (
                      PARTITION BY i.cod_aluno
                  ) AS quantidade_ingressos,
                  i.id AS numero_ingresso,
                  i.nome AS nome_participante,
                  i.telefone,
                  i.observacoes AS restricoes,
                  strftime('%d/%m/%Y %H:%M', i.data_compra) AS horario_e_dia_compra,
                  strftime('%d/%m/%Y', r.dia_bistro) AS dia_bistro,
                  i.valor_pago,
                  'Pago' AS status
           FROM Ingresso AS i
           INNER JOIN Aluno AS a
                   ON i.cod_aluno = a.cod_aluno
           INNER JOIN Reserva AS r
                   ON i.cod_reserva = r.cod_reserva
           WHERE i.foi_pago = 1
             AND (? IS NULL OR r.dia_bistro = ?)
           ORDER BY r.dia_bistro, i.data_compra DESC;
        ''',
        (dia_bistro, dia_bistro)
    )

    return cursor.fetchall()
