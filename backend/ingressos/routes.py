import os
import secrets
from time import time
from datetime import datetime
import mercadopago
import json
import hmac
import hashlib
import uuid

from ..banco_de_dados import get_db
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify

from .gerador_pdf import enviar_ingresso_por_email


routes = Blueprint('routes', __name__)

# Configuração do Mercado Pago

MP_ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]  # privado, só no backend
MP_PUBLIC_KEY = os.environ["MP_PUBLIC_KEY"]  # público, vai pro template/JS
MP_WEBHOOK_SECRET = os.environ["MP_WEBHOOK_SECRET"]

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# TODO: preço definido — R$130, crianças de 0 a 3 anos (tipo_ingresso == 0) não pagam
PRECO_INGRESSO = 130  # tipo_ingresso == 2


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


@routes.get('/lugares/confirmar_codigo')
def confirmar_codigo():
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
        if aluno['usos_restantes'] > 0:
            session['codigo'] = aluno['codigo']

            return jsonify({
                'sucesso': 'Código confirmado.',
                'usos': aluno["usos_restantes"]
            }), 200

        return jsonify({
            'erro': 'Não há usos restantes.'
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
            secrets.choice(CHARS_TOKEN)
            for _ in range(6)
        )

        existe = db.execute(
            'SELECT 1 FROM Ingresso WHERE token_QR = ?',
            (token,)
        ).fetchone()

        if existe is None:
            return token


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
                valor_ingresso = 0 # não pagantes
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            tokens_criados.append(token)

            a_pagar += valor_ingresso

        db.commit()

    except Exception as e:
        db.rollback()
        return jsonify({'erro': f'Erro ao criar ingressos: {e}.'}), 500

    session['tokens_criados'] = tokens_criados
    session['a_pagar'] = a_pagar

    return jsonify({'sucesso': 'Ingressos criados.'}), 201


@routes.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    codigo_aluno, lugares, a_pagar = session.get('codigo'), session.get('lugares'), session.get('a_pagar')

    if codigo_aluno is None:
        return jsonify({'erro': 'Nenhum código salvo.'}), 400
    if lugares is None:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400
    if a_pagar is None:
        return jsonify({'erro': 'Sem preço previsto para ser pago.'}), 400

    if request.method == 'POST':
        db = get_db()

        db.execute(
            '''
            UPDATE Aluno
            SET usos_restantes = usos_restantes - ?
            WHERE cod_aluno = ?
            ''',
            (len(lugares), codigo_aluno)
        )

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

    return render_template(
        'ingressos/pagamento.html',
        luagres=lugares,
        a_pagar=a_pagar,
        mp_public_key=MP_PUBLIC_KEY
    )


@routes.post('/pagamento')
def processar_pagamento():
    """
    Gera cobrança PIX no Mercado Pago.
    Body esperado:
    {
        "payer": {
            "email": "exemplo@email.com",
            "first_name": "Nome",
            "identification": {"type": "CPF", "number": "12345678900"}
        }
    }
    """
    if cronometro_expirado(session.get('cronometro_reservado')):
        return jsonify({'erro': 'A reserva expirou.'}), 409

    tokens_criados = session.get('tokens_criados', [])
    a_pagar = session.get('a_pagar')
    codigo_aluno = session.get('codigo')

    if not tokens_criados or a_pagar is None:
        return jsonify({'erro': 'Nenhum ingresso pendente de pagamento nesta sessão.'}), 400

    if a_pagar <= 0:
        # Nada a cobrar (ex: só ingressos gratuitos) — confirma direto
        _confirmar_ingressos_pagos(tokens_criados)
        return jsonify({'sucesso': True, 'status': 'approved'}), 200

    dados = request.get_json(force=True) or {}
    payer_input = dados.get('payer', {}) if isinstance(dados.get('payer'), dict) else {}

    email = payer_input.get('email') or dados.get('email')
    if not email:
        return jsonify({'erro': 'Dados de pagamento incompletos. O e-mail do pagador é obrigatório.'}), 400

    payer_data = {'email': email}

    if 'first_name' in payer_input:
        payer_data['first_name'] = payer_input['first_name']
    elif 'nome' in dados:
        payer_data['first_name'] = dados['nome']

    if 'last_name' in payer_input:
        payer_data['last_name'] = payer_input['last_name']

    if 'identification' in payer_input:
        payer_data['identification'] = payer_input['identification']
    elif 'cpf' in dados:
        payer_data['identification'] = {'type': 'CPF', 'number': dados['cpf']}

    referencia_externa = f"pedido_{uuid.uuid4().hex}"

    db = get_db()
    db.execute(
        '''
        INSERT INTO Pedido (referencia_externa, tokens, cod_aluno, valor, status, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (referencia_externa, json.dumps(tokens_criados), codigo_aluno, a_pagar, 'pending', datetime.now())
    )
    db.commit()

    request_options = mercadopago.config.RequestOptions()
    request_options.custom_headers = {
        'x-idempotency-key': str(uuid.uuid4()),
    }

    payment_data = {
        "transaction_amount": float(a_pagar),
        "description": "Compra de ingressos",
        "payment_method_id": "pix",
        "external_reference": referencia_externa,
        "payer": payer_data
    }

    try:
        resultado = sdk.payment().create(payment_data, request_options)
    except Exception as e:
        return jsonify({'erro': f'Falha ao comunicar com o Mercado Pago: {e}'}), 502

    payment = resultado.get('response', {})

    if resultado.get('status') not in (200, 201):
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            ('error', referencia_externa)
        )
        db.commit()
        return jsonify({'erro': 'Pagamento recusado ou inválido.', 'detalhes': payment}), 400

    payment_id = str(payment.get('id'))
    status = payment.get('status')

    db.execute(
        'UPDATE Pedido SET order_id = ? WHERE referencia_externa = ?',
        (payment_id, referencia_externa)
    )
    db.commit()

    if status in ('approved', 'processed'):
        _confirmar_ingressos_pagos(tokens_criados)
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            (status, referencia_externa)
        )
        db.commit()
        return jsonify({'sucesso': True, 'status': status}), 200

    if status in ('expired', 'canceled', 'rejected'):
        return jsonify({'erro': 'Pagamento não aprovado.', 'status': status}), 400

    # Extrai dados do PIX (QR Code e Copia e Cola)
    point_of_interaction = payment.get('point_of_interaction', {}) or {}
    transaction_data = point_of_interaction.get('transaction_data', {}) or {}

    return jsonify({
        'sucesso': True,
        'status': status,
        'id': payment.get('id'),
        'qr_code': transaction_data.get('qr_code'),
        'qr_code_base64': transaction_data.get('qr_code_base64'),
        'ticket_url': transaction_data.get('ticket_url')
    }), 200


def _confirmar_ingressos_pagos(tokens):
    """Marca os ingressos como pagos e envia por e-mail. Idempotente por token."""
    db = get_db()
    falhas_envio = []

    for token in tokens:
        ingresso = db.execute(
            'SELECT foi_pago FROM Ingresso WHERE token_QR = ?', (token,)
        ).fetchone()

        if ingresso is None or ingresso['foi_pago'] == 1:
            continue  # já processado ou não existe — não reenvia e-mail de novo

        db.execute('UPDATE Ingresso SET foi_pago = 1 WHERE token_QR = ?', (token,))
        db.commit()

        try:
            enviar_ingresso_por_email(token)
        except Exception as e:
            falhas_envio.append({'token': token, 'erro': str(e)})

    return falhas_envio


def _liberar_ingressos_nao_pagos(tokens, cod_aluno):
    """Pagamento recusado/expirado: libera lugares e desfaz o desconto usado."""
    db = get_db()

    for token in tokens:
        lugar = db.execute(
            'SELECT cod_lugar FROM Ingresso WHERE token_QR = ? AND foi_pago = 0',
            (token,)
        ).fetchone()

        if lugar is None:
            continue  # já foi pago em outra tentativa, ou não existe — não mexe

        db.execute('UPDATE Lugares SET ocupado = 0 WHERE cod_lugar = ?', (lugar['cod_lugar'],))
        db.execute('DELETE FROM Ingresso WHERE token_QR = ?', (token,))

    if cod_aluno:
        db.execute(
            'UPDATE Aluno SET usos_restantes = usos_restantes + ? WHERE cod_aluno = ?',
            (len(tokens), cod_aluno)
        )

    db.commit()


# Webhook — fonte de verdade sobre aprovação/recusa do PIX
def _validar_assinatura_webhook(req) -> bool:
    signature_header = req.headers.get('x-signature', '')
    request_id = req.headers.get('x-request-id', '')

    partes = dict(p.split('=', 1) for p in signature_header.split(',') if '=' in p)
    ts, v1 = partes.get('ts'), partes.get('v1')
    if not ts or not v1:
        return False

    corpo = req.get_json(silent=True) or {}
    data_id = req.args.get('data.id') or str(corpo.get('data', {}).get('id') or corpo.get('id') or '')
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"

    hmac_calculado = hmac.new(
        MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(hmac_calculado, v1)


@routes.post('/webhook/mercadopago')
def webhook_mercadopago():
    if not _validar_assinatura_webhook(request):
        return jsonify({'erro': 'assinatura inválida'}), 401

    corpo = request.get_json(silent=True) or {}
    topico = request.args.get('topic') or request.args.get('type') or corpo.get('type') or corpo.get('action')

    if topico and topico not in ('payment', 'payment.created', 'payment.updated', 'order'):
        return '', 200  # confirma recebimento para tópicos não gerenciados

    recurso_id = request.args.get('id') or request.args.get('data.id') or corpo.get('data', {}).get('id') or corpo.get('id')
    if not recurso_id:
        return '', 200

    try:
        resultado = sdk.payment().get(recurso_id)
    except Exception:
        return '', 200

    payment = resultado.get('response', {})

    status = payment.get('status')
    referencia_externa = payment.get('external_reference')

    db = get_db()
    pedido = None
    if referencia_externa:
        pedido = db.execute(
            'SELECT * FROM Pedido WHERE referencia_externa = ?', (referencia_externa,)
        ).fetchone()

    if pedido is None:
        pedido = db.execute(
            'SELECT * FROM Pedido WHERE order_id = ?', (str(recurso_id),)
        ).fetchone()

    if pedido is None:
        return '', 200  # não é um pedido nosso ou já foi limpo

    if pedido['status'] == status:
        return '', 200  # idempotência: já processamos essa mudança de status

    tokens = json.loads(pedido['tokens'])

    if status in ('approved', 'processed'):
        _confirmar_ingressos_pagos(tokens)
    elif status in ('expired', 'canceled', 'cancelled', 'rejected', 'refunded', 'charged_back'):
        _liberar_ingressos_nao_pagos(tokens, pedido['cod_aluno'])

    db.execute(
        'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
        (status, pedido['referencia_externa'])
    )
    db.commit()

    return '', 200


@routes.get('/pagamento/sucesso')
def pagamento_sucesso():
    tokens = session.get('tokens_criados')

    if not tokens:
        return redirect(url_for('routes.index'))

    db = get_db()
    placeholders = ','.join('?' for _ in tokens)
    ingressos = db.execute(
        f'SELECT nome, token_QR, foi_pago FROM Ingresso WHERE token_QR IN ({placeholders})',
        tokens
    ).fetchall()

    if not ingressos:
        return redirect(url_for('routes.index'))

    todos_pagos = all(i['foi_pago'] == 1 for i in ingressos)

    if todos_pagos:
        for chave in ('tokens_criados', 'a_pagar', 'lugares', 'cronometro_reservado', 'codigo'):
            session.pop(chave, None)

    return render_template(
        'ingressos/sucesso.html',
        ingressos=ingressos,
        pendente=not todos_pagos
    )


@routes.get('/pagamento/status')
def pagamento_status():
    """Endpoint leve pra fazer polling na tela de sucesso enquanto 'pendente' == True."""
    tokens = session.get('tokens_criados')
    if not tokens:
        return jsonify({'erro': 'Nenhum ingresso na sessão.'}), 400

    db = get_db()
    placeholders = ','.join('?' for _ in tokens)
    ingressos = db.execute(
        f'SELECT foi_pago FROM Ingresso WHERE token_QR IN ({placeholders})',
        tokens
    ).fetchall()

    todos_pagos = bool(ingressos) and all(i['foi_pago'] == 1 for i in ingressos)

    return jsonify({'pago': todos_pagos}), 200


@routes.get('/verificar_cronometro')
def verificar_cronometro():
    expirado = cronometro_expirado(session.get('cronometro_reservado'))

    if expirado:
        return jsonify({
            'expirado': True,
            'mensagem': 'O tempo da reserva expirou.'
        }), 410

    return jsonify({
        'expirado': False
    }), 200