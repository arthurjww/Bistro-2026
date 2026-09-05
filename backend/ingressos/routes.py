import secrets
from time import time
from datetime import datetime

from ..banco_de_dados import get_db
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify

from .gerador_pdf import enviar_ingresso_por_email


routes = Blueprint('routes', __name__)


def cronometro_expirado(cronometro):
    if cronometro is not None:
        return int(time() * 1000) >= cronometro
    return False


@routes.get('/')
def index():
    return render_template('ingressos/index.html')


@routes.get('/info_ingressos')
def informacoes():
    lugares, cronometro = session.get('lugares', []), session.get('cronometro_reservado')
    if not lugares or not cronometro:
        return redirect(url_for('/lugares'))

    return render_template(
        'ingressos/info_ingressos.html',
        cronometro=cronometro,
        quant=len(lugares),
        ingressos=lugares
    )


@routes.get('/info_ingressos/confirmar_codigo')
def confirmar_codigo():
    if cronometro_expirado(session.get('cronometro_reservado')):
        return jsonify({
            'erro': 'A reserva expirou.'
        }), 409

    lugares = session.get('lugares', [])

    if not lugares:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400

    codigo = request.args.get('codigo')
    db = get_db()

    aluno = db.execute(
        '''
        SELECT *
        FROM Aluno
        WHERE cod_aluno = ?
        ''',
        (codigo,)
    ).fetchone()

    if aluno is not None:
        quant_ingressos = len(lugares)

        if aluno['usos_restantes'] >= quant_ingressos:
            for lugar in lugares:
                db.execute(
                    'UPDATE Lugares SET cod_aluno = ? WHERE cod_lugar = ?',
                    (codigo, lugar)
                )

            db.commit()

            session['codigo'] = codigo

            return jsonify({
                'sucesso': 'Código confirmado.',
                'usos_restantes': f'{aluno["usos_restantes"] - quant_ingressos}.'
            }), 200

        return jsonify({
            'erro': '0 usos restantes.'
        }), 409

    return jsonify({
        'erro': 'Código não encontrado.'
    }), 404


# Chars que não são confudíveis, caso a adm precise digitar manualmente na hora
CHARS_TOKEN = 'ACDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz234679'

def _gerar_token_unico(db): 
    """Gera um token de 6 caracteres alfanuméricos único na tabela Ingresso."""
    while True: 
        token = ''.join(
            secrets.choice(CHARS_TOKEN) #string.ascii_uppercase + string.digits)
            for _ in range(6)
        )

        existe = db.execute(
            'SELECT 1 FROM Ingresso WHERE token_QR = ?',
            (token,)
        ).fetchone()

        if existe is None:
            return token


#TODO: Ver preço do ingresso
PRECO_INGRESSO = 100

@routes.post('/info_ingressos/criar_ingressos')
def criar_ingressos():
    if cronometro_expirado(session.get('cronometro_reservado')):
        return jsonify({
            'erro': 'A reserva expirou.'
        }), 409

    dados = request.get_json()

    if not dados or 'ingressos' not in dados: 
        return jsonify ({'erro': 'Dados de ingressos ausentes.'}), 400

    lugares_sessao = session.get('lugares', [])
    codigo_aluno = session.get('codigo')

    if not lugares_sessao:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400

    if not codigo_aluno:
        return jsonify ({'erro': 'Código de aluno não confirmado.'}), 400

    ingressos_enviados = dados['ingressos']

    if len(ingressos_enviados) != len(lugares_sessao):
        return jsonify({
            'erro':'Quantidade de ingressos não corresponde aos lugares reservados.'
        }), 400

    db = get_db()
    tokens_criados = []
    a_pagar = 0

    try: 
        for item, cod_lugar in zip (ingressos_enviados, lugares_sessao):

            nome = item.get('nome')
            email_envio = item.get('email_envio')

            if not nome or not email_envio:
                return jsonify({
                     'erro': 'Nome e email são obrigatórios para todos os ingressos.'
                }), 400

            tipo_ingresso = int(item.get('tipo_ingresso'))
            observacoes = item.get('observacoes')
            telefone = item.get('telefone')

            if tipo_ingresso == 0:
                valor_ingresso = 0
            elif tipo_ingresso == 1:
                valor_ingresso = PRECO_INGRESSO / 2
            else:
                valor_ingresso = PRECO_INGRESSO

            token = _gerar_token_unico(db)

            db.execute(
                '''
                INSERT INTO Ingresso (
                    nome, tipo_ingresso, observacoes, email_envio,
                    foi_pago, token_QR, utilizado, data_utilizado,
                    cod_aluno, cod_lugar, data_compra, telefone, valor_pago
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    nome,
                    tipo_ingresso,
                    observacoes,
                    email_envio,
                    0,          # foi_pago
                    token,
                    0,          # utilizado
                    None,       # data_utilizado
                    codigo_aluno,
                    cod_lugar,
                    datetime.now(),
                    telefone,
                    valor_ingresso
                )
            )

            db.execute(
                'UPDATE Lugares SET ocupado = 1 WHERE cod_lugar = ?',
                (cod_lugar,)
            )

            tokens_criados.append(token)

            a_pagar += valor_ingresso

        db.execute(
            '''
            UPDATE Aluno
            SET usos_restantes = usos_restantes - ?
            WHERE cod_aluno = ?
            ''',
            (len(tokens_criados), codigo_aluno)
        )

        db.commit()

    except Exception as e:
        db.rollback()
        return jsonify({'erro': f'Erro ao criar ingressos: {e}.'}), 500

    session['tokens_criados'] = tokens_criados
    session['a_pagar'] = a_pagar

    return jsonify({'sucesso': 'Ingressos criados.'}), 201


@routes.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    if request.method == 'POST':
        # ======================================================================
        # ENVIO DOS EMAILS
        # feito DEPOIS do commit: se o email falhar, os ingressos já criados
        # não são perdidos — só registramos a falha pra tratar depois.
        # ======================================================================
        db = get_db()
        tokens_criados = session.get('tokens_criados', [])

        falhas_envio = []

        for token in tokens_criados:
            db.execute(
                'UPDATE Ingresso SET foi_pago = 1 WHERE token_QR = ?',
                (token,)
            )
            try:
                enviar_ingresso_por_email(token)
            except Exception as e:
                falhas_envio.append({'token': token, 'erro': str(e)})

        db.commit()

        if falhas_envio:
            resposta = {
                'erro': 'Erro ao mandar email',
                'aviso': 'Ingressos criados, mas houve falha ao enviar alguns emails.',
                'falhas_envio': falhas_envio
            }
            return jsonify(resposta), 500

        return jsonify({
            'sucesso': 'Emails enviados com sucesso.',
            'tokens': tokens_criados
        }), 200

    lugares, a_pagar = session.get('lugares'), session.get('a_pagar')

    if not lugares:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400
    if not a_pagar:
        return jsonify({'erro': 'Sem preço previsto para ser pago.'}), 400

    return render_template(
        'ingressos/pagamento.html',
        luagres=lugares,
        a_pagar=a_pagar
    )


@routes.get('/verificar_cronometro')
def verificar_cronometro():
    expirado = cronometro_expirado(session.get('cronometro_expirado'))

    if expirado:
        return jsonify({
            'expirado': True,
            'mensagem': 'O tempo da reserva expirou.'
        }), 410

    return jsonify({
        'expirado': False
    }), 200