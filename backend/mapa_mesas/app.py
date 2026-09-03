from flask import Blueprint, jsonify, session
import mapa_mesas.lugares as lug

bp_lugares = Blueprint("lugares", __name__)

@bp_lugares.route("/api/mapa", methods=["GET"])
def rota_mapa():
    mapa = lug.listar_mapa()
    return jsonify(mapa)

@bp_lugares.route("/api/lugares/<cod_lugar>/escolher", methods=["POST"])
def rota_escolher(cod_lugar):
    cod_aluno = session.get("cod_aluno")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado"}), 401

    try:
        sucesso, motivo = lug.escolher_lugar(cod_lugar, cod_aluno)
    except lug.LugarInvalidoError as e:
        return jsonify({"erro": str(e)}), 400

    if not sucesso:
        return jsonify({"erro": motivo}), 409

    return jsonify({"ok": True, "status": "em_pagamento"})

@bp_lugares.route("/api/lugares/<cod_lugar>/confirmar", methods=["POST"])
def rota_confirmar(cod_lugar):
    cod_aluno = session.get("cod_aluno")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado."}), 401
 
    sucesso, motivo = lug.confirmar_pagamento(cod_lugar, cod_aluno)
    if not sucesso:
        return jsonify({"erro": motivo}), 409
 
    return jsonify({"ok": True, "status": "ocupado"})
 
 
@bp_lugares.route("/api/lugares/<cod_lugar>/cancelar", methods=["POST"])
def rota_cancelar(cod_lugar):
    cod_aluno = session.get("cod_aluno")
    if not cod_aluno:
        return jsonify({"erro": "Aluno não autenticado."}), 401
 
    sucesso, motivo = lug.cancelar_reserva(cod_lugar, cod_aluno)
    if not sucesso:
        return jsonify({"erro": motivo}), 409
 
    return jsonify({"ok": True, "status": "livre"})

if __name__ == "__main__":
    bp_lugares.run(debug=True)