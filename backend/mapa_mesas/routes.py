from flask import Blueprint, jsonify, session, render_template, request, redirect, url_for
from time import time

from backend.banco_de_dados import get_db
from backend.mapa_mesas.lugares import *

bp_lugares = Blueprint("lugares", __name__)

def verificar_db():
    db = get_db()
    data_exp = int(time() * 1000)

    reservas_exp = db.execute('''
        SELECT *
        FROM Reserva
        WHERE ocupado = ?
          AND cronometro_reservado <= ?
    ''', (EM_PAGAMENTO, data_exp)
    ).fetchall()

    for r in reservas_exp:
        ingresso = db.execute('''
            SELECT cod_aluno
            FROM Ingresso
            WHERE cod_lugar = ?
        ''', (r['cod_reserva'],)
        ).fetchone()
        db.execute(
            'DELETE FROM Ingresso WHERE cod_reserva = ?', (r['cod_reserva'],)
        )
        db.execute(
            'UPDATE Reserva SET ocupado = ? WHERE cod_reserva = ?', (LIVRE, r['cod_reserva'],)
        )
        if ingresso is not None:
            db.execute(
                'UPDATE Aluno SET usos_restantes = usos_restantes + ? WHERE cod_aluno = ?', (ingresso['cod_aluno'],)
            )

    db.commit()


@bp_lugares.route("/lugares", methods=["GET"])
def rota_mapa():
    verificar_db()
    saloes = listar_saloes_disponiveis()
    return render_template('mapa-mesas/bistrot.html', saloes_disponiveis=[salao.NUMERO_SALAO for salao in saloes]) #saloes disponiveis = informação para javascript

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
        if aluno['usos_restantes'] >= 0:    
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
        salao = qual_salao(cod_lugar)
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if salao is Salao2 and salao2_esta_oculto():
        return jsonify({"erro": "Salão 2 não disponível para este evento"}), 403

    try:
        sucesso, resultado = salao().escolher_lugar(cod_lugar, cod_aluno, dia_bistro)
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if not sucesso:
        # aqui "resultado" é a mensagem de erro
        return jsonify({"erro": resultado}), 409

    cod_reserva = resultado # resultado é igual a reserva do momento

    reservas = session.get('reservas', [])
    if cod_reserva not in reservas:
        reservas.append(cod_reserva)
    session['reservas'] = reservas

    return jsonify({"ok": True, 'reservas': reservas})

@bp_lugares.route("/lugares/seguir", methods=['GET'])
def seguir():
    cronometro = int(time() * 1000) + 15 * 60_000
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