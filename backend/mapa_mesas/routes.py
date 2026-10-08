from flask import Blueprint, jsonify, session, render_template, request, redirect, url_for
from time import time

from backend.banco_de_dados import get_db
from backend.mapa_mesas.lugares import *

bp_lugares = Blueprint("lugares", __name__)

def verificar_db():
    db = get_db()
    data_exp = int(time() * 1000)

    expiradas = db.execute("""
        SELECT cod_reserva, cod_aluno
        FROM Reserva
        WHERE ocupado = ?
          AND cronometro_reservado IS NOT NULL
          AND cronometro_reservado <= ?
    """, (EM_PAGAMENTO, data_exp)).fetchall()

    cod_reservas = [reserva["cod_reserva"] for reserva in expiradas]

    if not cod_reservas:
        return

    placeholders = ",".join("?" for _ in cod_reservas)

    ingressos = db.execute(
        f"SELECT cod_aluno FROM Ingresso WHERE cod_reserva IN ({placeholders})",
        cod_reservas
    ).fetchall()

    db.execute(
        f"DELETE FROM Ingresso WHERE cod_reserva IN ({placeholders})",
        cod_reservas
    )

    db.execute(
        f"UPDATE Reserva SET ocupado = ?, cronometro_reservado = NULL WHERE cod_reserva IN ({placeholders})",
        (LIVRE, *cod_reservas)
    )

    usos_por_aluno = {}

    for ingresso in ingressos:
        cod_aluno = ingresso["cod_aluno"]
        usos_por_aluno[cod_aluno] = usos_por_aluno.get(cod_aluno, 0) + 1

    for cod_aluno, quantidade in usos_por_aluno.items():
        db.execute(
            "UPDATE Aluno SET usos_restantes = usos_restantes + ? WHERE cod_aluno = ?",
            (quantidade, cod_aluno)
        )

    usos_reservas_por_aluno = {}

    for reserva in expiradas:
        cod_aluno = reserva["cod_aluno"]
        usos_reservas_por_aluno[cod_aluno] = (
            usos_reservas_por_aluno.get(cod_aluno, 0) + 1
        )

    for cod_aluno, quantidade in usos_reservas_por_aluno.items():
        db.execute(
            "UPDATE Aluno SET usos_restantes = usos_restantes + ?   WHERE cod_aluno = ?",
            (quantidade, cod_aluno)
        )       

    db.commit()

    reservas_sessao = set(session.get("reservas", []))

    if reservas_sessao.intersection(cod_reservas):
        for chave in (
            "reservas",
            "cronometro_reservado",
            "tokens_criados",
            "a_pagar",
            "referencia_externa_pagamento"
        ):
            session.pop(chave, None)


@bp_lugares.route("/lugares", methods=["GET"])
def rota_mapa():
    verificar_db()
    usos_restantes = None

    cod_aluno = session.get("codigo")
    usos_restantes = 0
    
    if cod_aluno:
        aluno = get_db().execute("""
            SELECT usos_restantes
            FROM Aluno 
            WHERE cod_aluno = ?
        """, (cod_aluno,)).fetchone()

        if aluno:
            usos_restantes = aluno["usos_restantes"]

    return render_template('mapa-mesas/bistrot.html', usos_restantes=usos_restantes) #saloes disponiveis = informação para javascript

@bp_lugares.route("/lugares/datas", methods=["GET"])
def listar_datas():
    linhas = get_db().execute("""
        SELECT data_dia_1, data_dia_2
        FROM Config
        ORDER BY id
    """).fetchall()

    datas = []
    for linha in linhas:
        for coluna in ("data_dia_1", "data_dia_2"):
            data = linha[coluna]
            if data and data not in datas:
                datas.append(data)

    return jsonify({"datas": datas}), 200

@bp_lugares.route("/lugares/mapa", methods=["GET"])
def listar_mapa():
    dia = request.args.get("dia")

    if not dia:
        return jsonify({"erro": "dia não informado"}), 400

    verificar_db()

    mapa = MapaLugares().listar_mapa(dia)
    lugares = [
        lugar
        for lugares_mesa in mapa.values()
        for lugar in lugares_mesa
    ]

    return jsonify({
        "dia": dia,
        "lugares": lugares
    }), 200

@bp_lugares.route("/lugares/confirmar_codigo", methods=['GET'])
def confirmar_codigo():
    codigo = request.args.get('codigo')
    
    aluno = get_db().execute(
        '''
        SELECT *
        FROM Aluno
        WHERE cod_aluno = ?
        ''',
        (codigo,)
    ).fetchone()

    if aluno is not None:
        if aluno['usos_restantes'] > 0:    
            session['codigo'] = codigo

            return jsonify({
                'sucesso': 'Código confirmado',
                'usos_restantes': aluno["usos_restantes"]
            }), 200

        return jsonify({
            'erro': '0 usos restantes'
        }), 409

    return jsonify({
        'erro': 'Código não encontrado'
    }), 404

@bp_lugares.route("/lugares/<cod_lugar>/escolher", methods=["POST"])
def rota_escolher(cod_lugar):
    cod_aluno = session.get("codigo")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado"}), 401

    dia_bistro = request.args.get("dia")
    if not dia_bistro:
        return jsonify({"erro": "dia_bistro não informado"}), 400

    try:
        sucesso, resultado = MapaLugares().escolher_lugar(
            cod_lugar, cod_aluno, dia_bistro
        )
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if not sucesso:
        # aqui "resultado" é a mensagem de erro
        return jsonify({"erro": resultado}), 409
    db = get_db()
    usos_restantes = db.execute("""
        UPDATE Aluno
        SET usos_restantes = usos_restantes - 1
        WHERE cod_aluno = ? AND usos_restantes > 0
    """, (cod_aluno,))
    if usos_restantes.rowcount == 0:
        db.rollback()
        return jsonify({"erro": "0 usos restantes"}), 409
    db.commit()

    cod_reserva = resultado # resultado é igual a reserva do momento

    reservas = session.get('reservas', [])
    if cod_reserva not in reservas:
        reservas.append(cod_reserva)
    session['reservas'] = reservas

    return jsonify({"ok": True, 'reservas': reservas})

@bp_lugares.route("/lugares/seguir", methods=['GET'])
def seguir():
    cronometro = int(time() * 1000) + 30 * 60_000
    reservas = session.get("reservas", [])
    cod_aluno = session.get("codigo")
    ocupado = EM_PAGAMENTO
    if not reservas:
        return jsonify({"erro": "Nenhum lugar selecionado"}), 400
    if not cod_aluno:
        return jsonify({"erro": "Aluno não identificado"}), 401

    db = get_db()
    for cod_reserva in reservas:
        get_db().execute(
            '''UPDATE Reserva 
                SET cronometro_reservado = ?
                WHERE cod_reserva = ?
                AND cod_aluno = ?
                AND ocupado = ?''', (cronometro, cod_reserva, cod_aluno, ocupado)
        )
    db.commit()
    session['cronometro_reservado'] = cronometro
    session.permanent = True
    return redirect(url_for('routes.informacoes'))

@bp_lugares.route("/lugares/liberar-reservas", methods=["POST"])
def liberar_reservas_da_sessao():
    cod_aluno = session.get("codigo")
    codigos_reserva = list(dict.fromkeys(session.get("reservas", [])))

    if not cod_aluno or not codigos_reserva:
        return jsonify({"ok": True}), 200

    db = get_db()
    placeholders = ",".join("?" for _ in codigos_reserva)

    try:
        reservas_pendentes = db.execute(
            f"""
            SELECT cod_reserva
            FROM Reserva
            WHERE cod_reserva IN ({placeholders})
              AND cod_aluno = ?
              AND ocupado = ?
            """,
            (*codigos_reserva, cod_aluno, EM_PAGAMENTO)
        ).fetchall()

        pendentes = [r["cod_reserva"] for r in reservas_pendentes]

        if not pendentes:
            db.commit()
            _limpar_dados_checkout_da_sessao()
            return jsonify({"ok": True}), 200

        placeholders_pendentes = ",".join("?" for _ in pendentes)

        # Se uma reserva já tiver ingresso pago, ela não deve voltar a ficar livre.
        ingressos_pagos = db.execute(
            f"""
            SELECT DISTINCT cod_reserva
            FROM Ingresso
            WHERE cod_reserva IN ({placeholders_pendentes})
              AND foi_pago = 1
            """,
            pendentes
        ).fetchall()

        reservas_pagas = [r["cod_reserva"] for r in ingressos_pagos]
        reservas_para_liberar = [
            codigo for codigo in pendentes
            if codigo not in reservas_pagas
        ]

        if reservas_pagas:
            placeholders_pagos = ",".join("?" for _ in reservas_pagas)
            db.execute(
                f"""
                UPDATE Reserva
                SET ocupado = ?, cronometro_reservado = NULL
                WHERE cod_reserva IN ({placeholders_pagos})
                  AND ocupado = ?
                """,
                (OCUPADO, *reservas_pagas, EM_PAGAMENTO)
            )

        ingressos_removidos = 0

        if reservas_para_liberar:
            placeholders_liberar = ",".join(
                "?" for _ in reservas_para_liberar
            )

            cursor = db.execute(
                f"""
                DELETE FROM Ingresso
                WHERE cod_reserva IN ({placeholders_liberar})
                  AND foi_pago = 0
                """,
                reservas_para_liberar
            )
            ingressos_removidos = cursor.rowcount

            db.execute(
                f"""
                UPDATE Reserva
                SET ocupado = ?, cronometro_reservado = NULL
                WHERE cod_reserva IN ({placeholders_liberar})
                  AND cod_aluno = ?
                  AND ocupado = ?
                """,
                (
                    LIVRE,
                    *reservas_para_liberar,
                    cod_aluno,
                    EM_PAGAMENTO
                )
            )

            # No código atual, há um débito ao escolher o lugar e outro
            # ao criar o ingresso. Por isso, a limpeza devolve os dois.
            usos_a_devolver = len(reservas_para_liberar) + ingressos_removidos
            db.execute(
                """
                UPDATE Aluno
                SET usos_restantes = usos_restantes + ?
                WHERE cod_aluno = ?
                """,
                (usos_a_devolver, cod_aluno)
            )

        db.commit()
        _limpar_dados_checkout_da_sessao()
        return jsonify({"ok": True}), 200

    except Exception:
        db.rollback()
        raise


def _limpar_dados_checkout_da_sessao():
    for chave in (
        "reservas",
        "cronometro_reservado",
        "tokens_criados",
        "a_pagar",
        "referencia_externa_pagamento"
    ):
        session.pop(chave, None)