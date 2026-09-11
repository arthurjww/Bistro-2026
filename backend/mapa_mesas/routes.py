from flask import Blueprint, jsonify, session, render_template, request, redirect, url_for
from time import time

from backend.banco_de_dados import get_db
from backend.mapa_mesas.lugares import *

bp_lugares = Blueprint("lugares", __name__)

def verificar_db():
    db = get_db()

    data_exp = int(time() * 1000)

    lugares_exp = db.execute('''
        SELECT *
        FROM Lugares
        WHERE ocupado = ?
          AND cronometro_reservado = ?
    ''', (1, data_exp)
    ).fetchall()

    for lugar in lugares_exp:
        cod_aluno = db.execute('''
            SELECT cod_aluno
            FROM Ingresso
            WHERE cod_lugar = ?
        ''', (lugar['cod_lugar'])
        )
        db.execute(
            'DELETE * FROM Ingresso WHERE cod_lugar = ?', (lugar['cod_lugar'],)
        )
        db.execute(
            'UPDATE Lugares SET ocupado = ? WHERE cod_lugar = ?', (lugar['cod_lugar'],)
        )
        db.execute(
            'UPDATE Aluno SET usos_restantes = usos_restantes + ? WHERE cod_aluno = ?', (1, cod_aluno)
        )


@bp_lugares.route("/lugares", methods=["GET"])
def rota_mapa():
    verificar_db()
    return render_template('mapa-mesas/bistrot.html')

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

@bp_lugares.route("lugares/<cod_lugar>/escolher", methods=["POST"])
def rota_escolher(cod_lugar):
    cod_aluno = session.get("cod_aluno")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado"}), 401

    try:
        sucesso, motivo = Salao().escolher_lugar(cod_lugar, cod_aluno)
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if not sucesso:
        return jsonify({"erro": motivo}), 409

    return jsonify({"ok": True, "ocupado": "em_pagamento"})

@bp_lugares.route("lugares/seguir", methods=['GET'])
def seguir():
    cronometro = int(time() * 1000) + 15 * 60_000
    get_db().execute(
        'UPDATE Lugares SET cronometro_reservado = ?', (cronometro,)
    )
    session['cronometro_reservado'] = cronometro
    session.permanent = True
    return redirect(url_for('routes.info_ingressos'))

@bp_lugares.route("lugares/<cod_lugar>/escolher", methods=["POST"])
def rota_escolher(cod_lugar):
    cod_aluno = session.get("cod_aluno")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado"}), 401

    try:
        salao = qual_salao(cod_lugar)
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if salao is Salao2 and salao2_esta_oculto():
        return jsonify({"erro": "Salão 2 não disponível para este evento"}), 403

    try:
        sucesso, motivo = salao().escolher_lugar(cod_lugar, cod_aluno)
    except LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if not sucesso:
        return jsonify({"erro": motivo}), 409

    return jsonify({"ok": True, "ocupado": "em_pagamento"})