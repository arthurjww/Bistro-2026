import os
import secrets
from time import time
from datetime import datetime, timedelta
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

PRECO_INGRESSO = 0.01

PIX_EXPIRACAO_MINUTOS = 35

# Status que a Payments API pode retornar para um pagamento Pix.
# https://www.mercadopago.com.br/developers/pt/docs/checkout-api/payment-management/status
STATUS_APROVADO = 'approved'
STATUS_PENDENTES = ('pending', 'in_process')
STATUS_FALHOU = ('rejected', 'cancelled', 'refunded', 'charged_back')


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


@routes.after_request
def adicionar_cabecalhos_no_cache(response):
    """
    Impede que o navegador armazene as páginas em cache,
    evitando que o usuário volte pelo histórico para telas antigas.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@routes.get('/info_ingressos')
def informacoes():
    reservas, cronometro = session.get('reservas', []), session.get('cronometro_reservado')
    if not reservas or not cronometro:
        return redirect(url_for('lugares.rota_mapa'))

    db = get_db()

    placeholders = ','.join('?' for _ in reservas)

    try:
        reservas_db = db.execute(
            f'''
            SELECT cod_lugar, dia_bistro
            FROM Reserva
            WHERE cod_reserva IN ({placeholders})
            ''',
            reservas
        ).fetchall()
    except Exception as e:
        print(f'Erro ao pegar reservas do db: {e}')
        return redirect(url_for('lugares.rota_mapa'))

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
    """Gera um token de 6 caracteres alfanuméricos único na tabela Ingresso.

    Chamada de dentro do try/except de criar_ingressos(), então uma falha de
    banco aqui já é capturada por quem chama — não precisa de try próprio.
    """
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
                valor_ingresso = round(PRECO_INGRESSO / 2, 2)
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

    try:
        _resetar_cronometro(reservas_sessao, db)
    except Exception as e:
        db.rollback()
        print(f'Erro ao resetar cronômetro em criar_ingressos: {e}')

    return jsonify({'sucesso': 'Ingressos criados.'}), 201


# Pagamento (Pix via Payments API — Checkout Transparente)

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
        return jsonify({'sucesso': True, 'status': STATUS_APROVADO}), 200

    dados = request.get_json(force=True) or {}
    payer_input = dados.get('payer', {}) if isinstance(dados.get('payer'), dict) else {}

    email = payer_input.get('email') or dados.get('email')
    if not email:
        return jsonify({'erro': 'Dados de pagamento incompletos. O e-mail do pagador é obrigatório.'}), 400

    payer_data = {'email': email}

    # Usa valor truthy (não só presença da chave) — a Mercado Pago rejeita
    # first_name/identification.number vazios ("", null) com property_value.
    first_name = payer_input.get('first_name') or dados.get('nome')
    if first_name:
        payer_data['first_name'] = first_name

    last_name = payer_input.get('last_name')
    if last_name:
        payer_data['last_name'] = last_name

    identificacao = payer_input.get('identification')
    if not identificacao and dados.get('cpf'):
        identificacao = {'type': 'CPF', 'number': dados['cpf']}

    if identificacao and identificacao.get('number'):
        payer_data['identification'] = {
            'type': identificacao.get('type', 'CPF'),
            'number': identificacao['number'],
        }

    referencia_externa = f"pedido_{uuid.uuid4().hex}"

    db = get_db()

    try:
        db.execute(
            '''
            INSERT INTO Pedido (referencia_externa, tokens, cod_aluno, valor, status, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (referencia_externa, json.dumps(tokens_criados), codigo_aluno, a_pagar, 'pending', datetime.now())
        )
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'erro': f'Erro ao registrar o pedido: {e}.'}), 500

    request_options = mercadopago.config.RequestOptions()
    request_options.custom_headers = {
        'x-idempotency-key': str(uuid.uuid4()),
    }

    data_expiracao = (
            datetime.now().astimezone() + timedelta(minutes=PIX_EXPIRACAO_MINUTOS)
    ).isoformat(timespec='milliseconds')

    payment_data = {
        "transaction_amount": round(a_pagar, 2),
        "description": "Ingressos Bistrô 2026",
        "payment_method_id": "pix",
        "external_reference": referencia_externa,
        "date_of_expiration": data_expiracao,
        "payer": payer_data,
    }

    try:

        resultado = sdk.payment().create(payment_data, request_options)

        #Comentário abaixo printa todos os status para verificar passo a passo via terminal
        #Usado para verificação dos testes referentes a API do mercado pago.
        '''
        print("PAYLOAD ENVIADO:")
        print(json.dumps(payment_data, indent=2, ensure_ascii=False))

        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4()),
        }

        resposta = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=headers,
            json=payment_data,
            timeout=30,
        )

        print("STATUS MP:", resposta.status_code)
        print("RESPOSTA MP:", resposta.text)

        resultado = {
            "status": resposta.status_code,
            "response": resposta.json(),
        }
        '''
    except Exception as e:
        try:
            db.execute(
                'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
                ('error', referencia_externa)
            )
            db.commit()
        except Exception as e_db:
            db.rollback()
            print(f'Erro ao marcar Pedido como error após falha na Mercado Pago: {e_db}')
        print(f'Erro ao criar pagamento Pix (referencia_externa={referencia_externa}): {e}')
        return jsonify({'erro': f'Falha ao comunicar com o Mercado Pago: {e}'}), 502

    payment = resultado.get('response', {})

    if resultado.get('status') not in (200, 201):
        try:
            db.execute(
                'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
                ('error', referencia_externa)
            )
            db.commit()
        except Exception as e_db:
            db.rollback()
            print(f'Erro ao marcar Pedido como error (status inesperado da Mercado Pago): {e_db}')
        print(f'Mercado Pago recusou a criação do pagamento (referencia_externa={referencia_externa}): {payment}')
        return jsonify({'erro': 'Não foi possível gerar o Pix.', 'detalhes': payment}), 400

    # order_id guarda o ID do pagamento na Payments API (payment_id) — mesmo
    # nome de coluna de antes (Orders API), mas agora é o id usado em
    # sdk.payment().get() no webhook e nos logs de diagnóstico.
    try:
        db.execute(
            'UPDATE Pedido SET order_id = ? WHERE referencia_externa = ?',
            (payment.get('id'), referencia_externa)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f'Erro ao salvar payment_id do Pedido {referencia_externa}: {e}')

    # Guardamos a referência pra /pagamento/status saber qual Pedido consultar
    session['referencia_externa_pagamento'] = referencia_externa

    status = payment.get('status')
    print(f'Pagamento Pix criado: id={payment.get("id")} referencia_externa={referencia_externa} status={status}')

    transaction_data = payment.get('point_of_interaction', {}).get('transaction_data', {})

    dados_pix = {
        'qr_code': transaction_data.get('qr_code'),               # código "copia e cola"
        'qr_code_base64': transaction_data.get('qr_code_base64'), # imagem do QR em base64
        'ticket_url': transaction_data.get('ticket_url'),
    }

    if status in STATUS_FALHOU:
        _liberar_ingressos_nao_pagos(tokens_criados, codigo_aluno)
        try:
            db.execute(
                'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
                (status, referencia_externa)
            )
            db.commit()
        except Exception as e:
            db.rollback()
            print(f'Erro ao atualizar Pedido {referencia_externa} para status {status}: {e}')
        return jsonify({'erro': 'Pix não pôde ser gerado.', 'status': status}), 400

    try:
        novo_cronometro = _resetar_cronometro(reservas, db)
    except Exception as e:
        db.rollback()
        print(f'Erro ao resetar cronômetro em processar_pagamento: {e}')
        novo_cronometro = session.get('cronometro_reservado')

    # Pix nunca vem "approved" na criação — fica em pending/in_process até o
    # pagador escanear e pagar. A confirmação definitiva vem do webhook.
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
        return jsonify({
            'erro': 'Nenhum pagamento pendente nesta sessão.'
        }), 400

    db = get_db()

    try:
        pedido = db.execute(
            '''
            SELECT status, order_id, tokens, cod_aluno
            FROM Pedido
            WHERE referencia_externa = ?
            ''',
            (referencia_externa,)
        ).fetchone()
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao consultar status do pagamento: {e}.'
        }), 500

    if pedido is None:
        return jsonify({'erro': 'Pedido não encontrado.'}), 404

    status = pedido['status']

    # Já aprovado no banco
    if status == STATUS_APROVADO:
        return jsonify({'pago': True}), 200

    # Ainda pendente: consulta diretamente o Mercado Pago
    if status == 'pending' and pedido['order_id']:
        try:
            resultado = sdk.payment().get(pedido['order_id'])
            payment = resultado.get('response', {})
            status_mp = payment.get('status')

            print(
                f'Consulta Mercado Pago: '
                f'id={pedido["order_id"]} status={status_mp}'
            )

            if status_mp and status_mp != status:

                tokens = json.loads(pedido['tokens'])

                if status_mp == STATUS_APROVADO:
                    _confirmar_ingressos_pagos(tokens)

                elif status_mp in STATUS_FALHOU:
                    _liberar_ingressos_nao_pagos(
                        tokens,
                        pedido['cod_aluno']
                    )

                db.execute(
                    '''
                    UPDATE Pedido
                    SET status = ?
                    WHERE referencia_externa = ?
                    ''',
                    (status_mp, referencia_externa)
                )
                db.commit()

                status = status_mp

        except Exception as e:
            print(
                f'Erro ao consultar pagamento '
                f'{pedido["order_id"]} no Mercado Pago: {e}'
            )

    # Já aprovado no banco
    if status == STATUS_APROVADO:
        try:
            tokens = json.loads(pedido['tokens'])
            _confirmar_ingressos_pagos(tokens)
        except Exception as e:
            print(
                f'Erro ao processar ingressos do pedido '
                f'{referencia_externa}: {e}'
            )

        return jsonify({'pago': True}), 200

    if status in STATUS_FALHOU or status == 'error':
        return jsonify({
            'pago': False,
            'falhou': True,
            'status': status
        }), 200

    return jsonify({'pago': False}), 200


def _liberar_ingressos_nao_pagos(tokens, codigo_aluno):
    """Desfaz os ingressos de um Pix que falhou/expirou/foi recusado.

    Remove os Ingresso ainda não pagos (foi_pago=0) e devolve os usos ao
    Aluno. O lugar (Reserva) continua reservado até o cronômetro expirar
    naturalmente, pra não derrubar o usuário no meio de uma nova tentativa.
    """
    db = get_db()

    try:
        placeholders = ','.join('?' for _ in tokens)
        db.execute(
            f'DELETE FROM Ingresso WHERE token_QR IN ({placeholders}) AND foi_pago = 0',
            tokens
        )
        db.execute(
            'UPDATE Aluno SET usos_restantes = usos_restantes + ? WHERE cod_aluno = ?',
            (len(tokens), codigo_aluno)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f'Erro ao liberar ingressos não pagos (cod_aluno={codigo_aluno}): {e}')

def _confirmar_ingressos_pagos(tokens):
    """Marca ingressos como pagos e envia os PDFs por e-mail."""

    db = get_db()
    falhas = []

    for token in tokens:
        try:
            ingresso = db.execute(
                '''
                SELECT foi_pago
                FROM Ingresso
                WHERE token_QR = ?
                ''',
                (token,)
            ).fetchone()

            if ingresso is None:
                falhas.append({
                    'token': token,
                    'erro': 'Ingresso não encontrado.'
                })
                continue

            # Marca como pago apenas se ainda não estiver pago
            if ingresso['foi_pago'] == 0:
                db.execute(
                    '''
                    UPDATE Ingresso
                    SET foi_pago = 1
                    WHERE token_QR = ?
                    ''',
                    (token,)
                )

                # Busca a reserva através do próprio ingresso
                reserva = db.execute(
                    '''
                    SELECT cod_reserva
                    FROM Ingresso
                    WHERE token_QR = ?
                    ''',
                    (token,)
                ).fetchone()

                if reserva and reserva['cod_reserva']:
                    db.execute(
                        '''
                        UPDATE Reserva
                        SET ocupado = 1
                        WHERE cod_reserva = ?
                        ''',
                        (reserva['cod_reserva'],)
                    )

                db.commit()

            # Envia o e-mail mesmo se o ingresso já estiver pago.
            # Isso permite tentar novamente caso o envio anterior tenha falhado.
            try:
                enviar_ingresso_por_email(token)
                print(f'✅ E-mail enviado para o ingresso {token}')

            except Exception as e:
                print(f'❌ Erro ao enviar e-mail para {token}: {e}')
                falhas.append({
                    'token': token,
                    'erro': str(e)
                })

        except Exception as e:
            db.rollback()
            print(f'❌ Erro ao confirmar ingresso {token}: {e}')
            falhas.append({
                'token': token,
                'erro': str(e)
            })

    return falhas

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
    topico = request.args.get('type') or corpo.get('type')

    # Checkout Transparente (Payments API) manda notificações com type=payment,
    # não type=order. Notificações de outros tópicos (ex: merchant_order, que
    # a conta pode receber mesmo sem usar a Orders API) são ignoradas aqui.
    if topico != 'payment':
        return '', 200  # confirma recebimento, senão o Mercado Pago reenvia

    recurso_id = corpo.get('data', {}).get('id') or request.args.get('data.id')
    if not recurso_id:
        print('Webhook de payment recebido sem id do recurso.')
        return '', 200

    try:
        resultado = sdk.payment().get(recurso_id)
    except Exception as e:
        print(f'Erro ao consultar payment {recurso_id} na Mercado Pago: {e}')
        # 500 faz a Mercado Pago reenviar a notificação mais tarde.
        return '', 500

    payment = resultado.get('response', {})

    status = payment.get('status')
    referencia_externa = payment.get('external_reference')

    print(f'Webhook payment recebido: id={recurso_id} referencia_externa={referencia_externa} status={status}')

    db = get_db()

    try:
        pedido = db.execute(
            'SELECT * FROM Pedido WHERE referencia_externa = ?', (referencia_externa,)
        ).fetchone()
    except Exception as e:
        print(f'Erro ao consultar Pedido {referencia_externa} no webhook: {e}')
        return '', 500

    if pedido is None:
        print(f'Webhook: nenhum Pedido encontrado para referencia_externa={referencia_externa}')
        return '', 200  # não é um pedido nosso ou já foi limpo

    if pedido['status'] == status:
        return '', 200  # idempotência: já processamos essa mudança de status

    tokens = json.loads(pedido['tokens'])

    if status == STATUS_APROVADO:
        _confirmar_ingressos_pagos(tokens)
    elif status in STATUS_FALHOU:
        _liberar_ingressos_nao_pagos(tokens, pedido['cod_aluno'])

    try:
        db.execute(
            'UPDATE Pedido SET status = ? WHERE referencia_externa = ?',
            (status, referencia_externa)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f'Erro ao atualizar status do Pedido {referencia_externa}: {e}')
        # Os ingressos já podem ter sido confirmados/liberados acima (ambas as
        # funções são idempotentes por token). Retornamos 500 pra MP reenviar;
        # na próxima tentativa "pedido['status'] == status" ainda vai ser False,
        # então o UPDATE será tentado de novo sem duplicar e-mails já enviados.
        return '', 500

    return jsonify({'status': status}), 200


@routes.get('/pagamento/sucesso')
def pagamento_sucesso():
    # Esquema para armazenar reservas na session para caso /pagamento/sucesso receba um request de novo,
    # mas que impossibilite da pessoa continuar com a key 'reservas' na sessão, para que ela não possa
    # passar por /lugares e depois para /info_ingressos,
    # o que a faria ter que prencher os dados do ingresso novamente
    reservas_confirmadas = session.get('reservas_musica', [])
    reservas_sessao = session.get('reservas', [])

    if not reservas_sessao and not reservas_confirmadas:
        return redirect(url_for('lugares.rota_mapa'))

    if not reservas_confirmadas:
        session['reservas_musica'] = reservas_sessao

    if not reservas_sessao:
        reservas_sessao = reservas_confirmadas

    for chave in (
        'reservas',
        'cronometro_reservado',
        'tokens_criados',
        'a_pagar',
        'referencia_externa_pagamento'
    ):
        session.pop(chave, None)

    db = get_db()
    placeholders = ','.join('?' for _ in reservas_sessao)

    try:
        reservas = db.execute(
            f'SELECT ocupado FROM Reserva WHERE cod_reserva in ({placeholders})',
            reservas_sessao
        ).fetchall()
        ingressos = db.execute(
            f'SELECT foi_pago FROM Ingresso WHERE cod_reserva IN ({placeholders})',
            reservas_sessao
        ).fetchall()
    except Exception as e:
        print(f'Erro ao consultar dados em /pagamento/sucesso: {e}')
        return redirect(url_for('lugares.rota_mapa'))

    if not all(r['ocupado'] == 1 for r in reservas):
        return redirect(url_for('lugares.rota_mapa'))

    if not all(i['foi_pago'] == 1 for i in ingressos):
        return redirect(url_for('lugares.rota_mapa'))

    return redirect(os.getenv('MUSICAS_REDIRECT_URL', 'https://musicas.sinestesiabistro.com.br'))


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