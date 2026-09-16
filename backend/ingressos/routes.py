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
PIX_EXPIRACAO = "PT30M"  # 30 minutos


def _cronometro_expirado(cronometro):
    # retornar True significa que o cronometro expirou
    if cronometro is None:
        return True
    return int(time() * 1000) >= cronometro


def _resetar_cronometro(reservas, db):
    cronometro = int(time()) * 1000 + 30 * 60_000

    placeholders = ','.join('?' for _ in reservas)
    db.execute(
        f'''
        UPDATE Reserva
        SET cronometro_reservado = ?
        WHERE cod_reserva in ({placeholders})
        ''', (cronometro, *reservas)
    )
    db.commit()

    session['cronometro_reservado'] = cronometro

    return cronometro


@routes.get('/')
def index():
    return render_template('ingressos/index.html')


@routes.get('/info_ingressos')
def informacoes():
    reservas, cronometro = session.get('reservas', []), session.get('cronometro_reservado')
    if not reservas or not cronometro:
        return redirect(url_for('lugares.rota_mapa'))

    db = get_db()

    placeholders = ','.join('?' for _ in reservas)

    reservas_db = db.execute(
        f'''
        SELECT cod_lugar, dia_bistro
        FROM Reserva
        WHERE cod_reserva IN ({placeholders})
        ''',
        reservas
    ).fetchall()

    if len(reservas_db) != len(reservas):
        return redirect(url_for('lugares.rota_mapa'))

    lugares_dias = [
        (r['cod_lugar'], r['dia_bistro']) for r in reservas_db
    ]

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
    if _cronometro_expirado(session.get('cronometro_reservado')):
        return jsonify({
            'erro': 'A reserva expirou.'
        }), 409

    dados = request.get_json()

    if not dados or 'ingressos' not in dados:
        return jsonify({'erro': 'Dados de ingressos ausentes.'}), 400

    reservas_sessao = session.get('reservas', [])
    codigo_aluno = session.get('codigo')

    if not reservas_sessao:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400

    if not codigo_aluno:
        return jsonify({'erro': 'Código de aluno não confirmado.'}), 400

    ingressos_enviados = dados['ingressos']

    if len(ingressos_enviados) != len(reservas_sessao):
        return jsonify({
            'erro': 'Quantidade de ingressos não corresponde aos lugares reservados.'
        }), 400

    db = get_db()
    tokens_criados = []
    a_pagar = 0

    try:
        for item, cod_reserva in zip(ingressos_enviados, reservas_sessao):

            nome = item.get('nome')
            email_envio = item.get('email_envio')

            if not nome or not email_envio:
                return jsonify({
                     'erro': 'Nome e email são obrigatórios para todos os ingressos.'
                }), 400

            tipo_ingresso= item.get('tipo_ingresso')
            try:
                # melhor int do que float, pois valor não tem casas decimais
                # e float costuma ser instável em cálculos e.g. 0.1 + 0.2 != 0.3
                tipo_ingresso = int(tipo_ingresso)
            except (TypeError, ValueError):
                return jsonify({
                    'erro': f'tipo_ingresso inválido para o ingresso de "{nome}".'
                }), 400

            observacoes = item.get('observacoes')
            telefone = item.get('telefone')

            if tipo_ingresso == 0:
                valor_ingresso = 0  # não pagantes
            elif tipo_ingresso == 1:
                valor_ingresso = PRECO_INGRESSO // 2
            else:
                valor_ingresso = PRECO_INGRESSO

            token = _gerar_token_unico(db)

            db.execute(
                '''
                INSERT INTO Ingresso (
                    nome, tipo_ingresso, observacoes, email_envio,
                    foi_pago, token_QR, utilizado, data_utilizado,
                    cod_aluno, cod_reserva, data_compra, telefone, valor_pago
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
                    cod_reserva,
                    datetime.now(),
                    telefone,
                    valor_ingresso
                )
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

    session['a_pagar'] = a_pagar
    session['tokens_criados'] = tokens_criados
    _resetar_cronometro(reservas_sessao, db)

    return jsonify({'sucesso': 'Ingressos criados.'}), 201


# Pagamento (Pix via Orders API)

@routes.get('/pagamento')
def pagamento():
    codigo_aluno, reservas, a_pagar, cronometro = (
        session.get('codigo'), session.get('reservas', []),
        session.get('a_pagar'), session.get('cronometro_reservado')
    )

    if None in (codigo_aluno, a_pagar, cronometro) or not reservas:
        return redirect(url_for('lugares.rota_mapa'))

    # A tela só precisa coletar os dados do pagador e chamar POST /pagamento
    # o QR code do Pix vem na resposta desse POST

    return render_template(
        'ingressos/pagamento.html',
        cronometro=cronometro,
        reservas=len(reservas),
        a_pagar=a_pagar
    )


@routes.post('/pagamento')
def processar_pagamento():
    """
    Cria o pedido Pix na Mercado Pago e devolve o QR code pro frontend exibir.
    Body esperado:
    {
        "payer": {
            "email": "cliente@email.com",
            "first_name": "Nome",
            "identification": {"type": "CPF", "number": "00000000000"}
        }
    }
    """

    if _cronometro_expirado(session.get('cronometro_reservado')):
        return jsonify({'erro': 'A reserva expirou.'}), 409

    tokens_criados = session.get('tokens_criados', [])
    reservas = session.get('reservas', [])
    a_pagar = session.get('a_pagar')
    codigo_aluno = session.get('codigo')

    if not tokens_criados or not reservas or a_pagar is None:
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
        return jsonify({'erro': f'Falha ao comunicar com o Mercado Pago: {e}'}), 502

    order = resultado.get('response', {})

    if resultado.get('status') not in (200, 201):
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            ('error', referencia_externa)
        )
        db.commit()
        return jsonify({'erro': 'Não foi possível gerar o Pix.', 'detalhes': order}), 400

    db.execute(
        'UPDATE Pedido SET order_id = ? WHERE referencia_externa = ?',
        (order.get('id'), referencia_externa)
    )
    db.commit()

    # Guardamos a referência pra /pagamento/status saber qual Pedido consultar
    session['referencia_externa_pagamento'] = referencia_externa

    status = order.get('status')

    pagamento_info = (order.get('transactions', {}).get('payments') or [{}])[0]
    payment_method_resp = pagamento_info.get('payment_method', {})

    dados_pix = {
        'qr_code': payment_method_resp.get('qr_code'),               # código "copia e cola"
        'qr_code_base64': payment_method_resp.get('qr_code_base64'), # imagem do QR em base64
        'ticket_url': payment_method_resp.get('ticket_url'),
    }

    if status in ('expired', 'canceled', 'rejected'):
        return jsonify({'erro': 'Pix não pôde ser gerado.', 'status': status}), 400

    novo_cronometro = _resetar_cronometro(reservas, db)

    # Pix nunca vem "processed" na criação — fica em action_required/pending
    # até o pagador escanear e pagar. A confirmação definitiva vem do webhook.
    return jsonify({
        'sucesso': True,
        'status': status,
        'pendente': True,
        'cronometro': novo_cronometro,
        'pix': dados_pix,
    }), 202


@routes.get('/pagamento/status')
def pagamento_status():
    referencia_externa = session.get('referencia_externa_pagamento')

    if not referencia_externa:
        return jsonify({'erro': 'Nenhum pagamento pendente nesta sessão.'}), 400

    db = get_db()
    pedido = db.execute(
        'SELECT status FROM Pedido WHERE referencia_externa = ?', (referencia_externa,)
    ).fetchone()

    if pedido is None:
        return jsonify({'erro': 'Pedido não encontrado.'}), 404

    status = pedido['status']

    if status == 'processed':
        return jsonify({'pago': True}), 200

    if status in ('expired', 'canceled', 'rejected', 'error'):
        return jsonify({'pago': False, 'falhou': True, 'status': status}), 200

    # ainda 'pending' / 'action_required' — o webhook não confirmou nada ainda
    return jsonify({'pago': False}), 200


def _confirmar_ingressos_pagos(tokens):
    """Marca os ingressos como pagos e envia por e-mail. Idempotente por token."""
    db = get_db()
    falhas_envio = []

    for token in tokens:
        ingresso = db.execute(
            'SELECT foi_pago, cod_reserva FROM Ingresso WHERE token_QR = ?', (token,)
        ).fetchone()

        if ingresso is None or ingresso['foi_pago'] == 1:
            continue  # já processado ou não existe — não reenvia e-mail de novo

        db.execute('UPDATE Ingresso SET foi_pago = 1 WHERE token_QR = ?', (token,))
        db.execute('UPDATE Reserva SET ocupado = 1 WHERE cod_reserva = ?', (ingresso['cod_reserva'],))
        db.commit()

        try:
            enviar_ingresso_por_email(token)
        except Exception as e:
            falhas_envio.append({'token': token, 'erro': str(e)})

    return falhas_envio


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
    # aparentemente, order está em type e não topic
    topico = request.args.get('type') or corpo.get('type')

    # O pagamento é criado pela Orders API (sdk.order().create()).
    # Para esse fluxo, processamos apenas notificações do tópico 'order',
    # pois o data.id recebido nesse tópico é o ID da Order e pode ser
    # consultado com sdk.order().get().
    #
    # Notificações do tópico 'payment' possuem o ID de um pagamento,
    # que deve ser consultado pela API de pagamentos, não pela API de orders.
    # Como este fluxo usa a Order como fonte de verdade, ignoramos 'payment'.
    if topico != 'order':
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

    db.execute(
        'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
        (status, referencia_externa)
    )
    db.commit()

    return jsonify({'status': status}), 200


@routes.get('/pagamento/sucesso')
def pagamento_sucesso():
    reservas = session.get('reservas', [])

    if not reservas:
        return redirect(url_for('lugares.rota_mapa'))

    db = get_db()
    placeholders = ','.join('?' for _ in reservas)
    ingressos = db.execute(
        f'SELECT nome, token_QR FROM Ingresso WHERE token_QR IN ({placeholders})',
        reservas
    ).fetchall()

    if len(reservas) != len(ingressos):
        return redirect(url_for('lugares.rota_mapa'))

    return render_template(
        'ingressos/sucesso.html',
        ingressos=ingressos,
    )


@routes.get('/verificar_cronometro')
def verificar_cronometro():
    expirado = _cronometro_expirado(session.get('cronometro_reservado'))

    if expirado:
        return jsonify({
            'expirado': True,
            'mensagem': 'O tempo da reserva expirou.'
        }), 410

    return jsonify({
        'expirado': False
    }), 200