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
MP_WEBHOOK_SECRET = os.environ["MP_WEBHOOK_SECRET"]

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# TODO: preço definido — R$130, crianças de 0 a 3 anos (tipo_ingresso == 0) não pagam
PRECO_INGRESSO = 130  # tipo_ingresso == 2

# Tempo que o QR code do Pix fica válido (ISO 8601 duration).
# Ajuste para bater com o tempo do seu cronômetro de reserva de lugar.
PIX_EXPIRACAO = "PT30M"  # 30 minutos


def cronometro_expirado(cronometro):
    if cronometro is not None:
        return int(time() * 1000) >= cronometro
    return False


@routes.get('/')
def index():
    return render_template('ingressos/index.html')


@routes.get('/info_ingressos')
def informacoes():
    reservas, cronometro = session.get('reservas', []), session.get('cronometro_reservado')
    if not reservas or not cronometro:
        return redirect(url_for('lugares.rota_mapa'))

    lugares_dias = []
    db = get_db()

    for cod_reserva in reservas:
        reserva = db.execute(
            '''
            SELECT cod_lugar, dia_bistro
            FROM Reserva
            WHERE cod_reserva = ?
            ''', (cod_reserva,)
        ).fetchone()

        if reserva is None:
            session.clear()
            return redirect(url_for('lugares.rota_mapa'))

        lugares_dias.append((reserva['cod_luagr'], reserva['dia_bistro']))

    return render_template(
        'ingressos/info_ingressos.html',
        cronometro=cronometro,
        quant=len(lugares_dias),
        ingressos=lugares_dias
    )


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

            # sem isso o lugar nunca fica ocupado e outra pessoa pode reservar
            # o mesmo assento enquanto o pagamento está em aberto.
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


# Pagamento (Pix via Orders API)

@routes.get('/pagamento')
def pagamento():
    codigo_aluno, lugares, a_pagar = session.get('codigo'), session.get('lugares'), session.get('a_pagar')

    if codigo_aluno is None:
        return jsonify({'erro': 'Nenhum código salvo.'}), 400
    if lugares is None:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400
    if a_pagar is None:
        return jsonify({'erro': 'Sem preço previsto para ser pago.'}), 400

    # A tela só precisa coletar o e-mail do pagador e chamar POST /pagamento
    # o QR code do Pix vem na resposta desse POST

    return render_template(
        'ingressos/pagamento.html',
        lugares=lugares,
        a_pagar=a_pagar
    )


@routes.post('/pagamento')
def processar_pagamento():
    """
    Cria o pedido Pix na Mercado Pago e devolve o QR code pro frontend exibir.
    Body esperado:
    {
        "email_pagador": "cliente@email.com"
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
        # Nada a cobrar (ex: só ingressos gratuitos) — confirma direto, sem Mercado Pago
        _confirmar_ingressos_pagos(tokens_criados)
        return jsonify({'sucesso': True, 'status': 'processed'}), 200

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

    order_data = {
        "type": "online",
        "total_amount": f"{a_pagar:.2f}",
        "external_reference": referencia_externa,
        "processing_mode": "automatic",
        "transactions": {
            "payments": [
                {
                    "amount": f"{a_pagar:.2f}",
                    "payment_method": {
                        "id": "pix",
                        "type": "bank_transfer",
                    },
                    "expiration_time": PIX_EXPIRACAO,
                }
            ]
        },
        "payer": payer_data
    }

    try:
        resultado = sdk.order().create(order_data, request_options)
    except Exception as e:
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            ('error', referencia_externa)
        )
        db.commit()
        _liberar_ingressos_nao_pagos(tokens_criados, codigo_aluno)

        return jsonify({'erro': f'Falha ao comunicar com o Mercado Pago: {e}'}), 502

        
    order = resultado.get('response', {})

    if resultado.get('status') not in (200, 201):
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            ('error', referencia_externa)
        )
        db.commit()
        _liberar_ingressos_nao_pagos(tokens_criados, codigo_aluno)
        return jsonify({'erro': 'Não foi possível gerar o Pix.', 'detalhes': order}), 400

    db.execute(
        'UPDATE Pedido SET order_id = ? WHERE referencia_externa = ?',
        (order.get('id'), referencia_externa)
    )
    db.commit()

    status = order.get('status')

    pagamento_info = (order.get('transactions', {}).get('payments') or [{}])[0]
    payment_method_resp = pagamento_info.get('payment_method', {})

    dados_pix = {
        'qr_code': payment_method_resp.get('qr_code'),               # código "copia e cola"
        'qr_code_base64': payment_method_resp.get('qr_code_base64'), # imagem do QR em base64
        'ticket_url': payment_method_resp.get('ticket_url'),
    }

    if status in ('expired', 'canceled', 'rejected'):
        _liberar_ingressos_nao_pagos(tokens_criados, codigo_aluno)
        return jsonify({'erro': 'Pix não pôde ser gerado.', 'status': status}), 400

    # Pix nunca vem "processed" na criação — fica em action_required/pending
    # até o pagador escanear e pagar. A confirmação definitiva vem do webhook.
    return jsonify({
        'sucesso': True,
        'status': status,
        'pendente': True,
        'pix': dados_pix,
    }), 202

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
        reserva = db.execute(
            'SELECT cod_reserva FROM Ingresso WHERE token_QR = ? AND foi_pago = 0',
            (token,)
        ).fetchone()

        if reserva is None:
            continue  # já foi pago em outra tentativa, ou não existe — não mexe

        db.execute('DELETE FROM Reserva WHERE cod_reserva = ?', (reserva['cod_reserva'],))
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

    data_id = req.args.get('data.id', '')
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
    topico = request.args.get('topic') or corpo.get('type')

    if topico not in ('payment', 'order'):
        return '', 200  # confirma recebimento, senão o Mercado Pago reenvia

    recurso_id = corpo.get('data', {}).get('id')
    if not recurso_id:
        return '', 200

    resultado = sdk.order().get(recurso_id)
    order = resultado.get('response', {})

    status = order.get('status')
    referencia_externa = order.get('external_reference')

    db = get_db()
    pedido = db.execute(
        'SELECT * FROM Pedido WHERE referencia_externa = ?', (referencia_externa,)
    ).fetchone()


    if pedido is None:
        return '', 200  # não é um pedido nosso ou já foi limpo

    if pedido['status'] == status:
        return '', 200  # idempotência: já processamos essa mudança de status

    tokens = json.loads(pedido['tokens'])

    if status == 'processed':
        _confirmar_ingressos_pagos(tokens)
    elif status in ('expired', 'canceled', 'rejected'):
        _liberar_ingressos_nao_pagos(tokens, pedido['cod_aluno'])

    db.execute(
        'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
        (status, referencia_externa)
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