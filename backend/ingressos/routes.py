from ..banco_de_dados import get_db
from flask import Blueprint, request, session, flash, redirect, url_for, render_template, jsonify
from flask_login import current_user


routes = Blueprint('routes', __name__)


def cronometro_expirado():
    lugares = session.get('ingressos', [])

    lugar_db = get_db().execute(
        '''
        SELECT cronometro_reservado
        FROM Lugares
        WHERE cod_lugar = ?
        ''',
        (lugares[0])
    ).fetchone()

    if lugar_db is not None:
        cronometro = lugar_db[4]


@routes.get('/')
def index():
    return render_template('ingressos/index.html', logado=current_user.is_authenticated)


@routes.get('/info_ingressos')
def informacoes():
    lugares = session.get('lugares', [])

    lugar_db = get_db().execute(
        '''
        SELECT cronometro_reservado
        FROM Lugares
        WHERE cod_lugar = ?
        ''',
        (lugares[0])
    ).fetchone()

    if lugar_db is not None:
        cronometro = lugar_db[4]
        return render_template(
            'info_ingressos',
            cronometro=cronometro,
            quant=len(lugares),
            ingressos=lugares
        )

    return redirect(url_for('/lugares'))


@routes.post('/info_ingressos/confirmar_codigo')
def confirmar_codigo():
    dados = request.get_json()

    if dados['cronometro'] <= 0:
        return redirect(url_for('/lugares'))

    codigo = dados['codigo']

    aluno = get_db().execute(
        '''
        SELECT *
        FROM Aluno
        WHERE cod_aluno = ?
        ''',
        (codigo,)
    ).fetchone()

    if aluno is not None:
        quant_ingressos = len(session.get('lugares', []))

        if aluno[2] >= quant_ingressos:

            session['codigo'] = codigo
            return jsonify({
                'sucesso': 'Código confirmado'
            }), 200

        return jsonify({
            'erro': '0 usos restantes'
        }), 409

    return jsonify({
        'erro': 'Código não encontrado'
    }), 404


@routes.post('/info/ingressos/criar_ingressos')
def criar_ingressos():
    pass