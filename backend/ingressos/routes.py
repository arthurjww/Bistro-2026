import secrets
from datetime import datetime, timedelta

from ..banco_de_dados import get_db
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from flask_login import current_user

from .gerador_pdf import enviar_ingresso_por_email


routes = Blueprint('routes', __name__)


def cronometro_expirado():
    lugares = session.get('ingressos', [])

    lugar_db = get_db().execute(
        '''
        SELECT cronometro_reservado
        FROM Lugares
        WHERE cod_lugar = ?
        ''', 
        (lugares[0],)
    ).fetchone()

    if lugar_db is not None:
        cronometro = lugar_db['cronometro_reservado']
        return datetime.now() >= cronometro + timedelta(minutes=15)

    return False


@routes.get('/')
def index():
    return render_template(
        'ingressos/index.html',
        logado=current_user.is_authenticated
    )


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
        cronometro = lugar_db[0]
        return render_template(
            'info_ingressos',
            cronometro=cronometro,
            quant=len(lugares),
            ingressos=lugares
        )

    return redirect(url_for('/lugares'))


@routes.post('/info_ingressos/confirmar_codigo')
def confirmar_codigo():
    if cronometro_expirado():
        return jsonify({
            'erro': 'A reserva expirou.'
        }), 409

    dados = request.get_json()
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

        if aluno['usos_restantes'] >= quant_ingressos:

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



#TODO: Acredito não ser necessário, pois o banco de dados automaticamente incrementa
def _proximo_id_ingresso(db):
    """Retorna o próximo id sequencial (quantidade de ingressos + 1)"""

    resultado = db.execute('SELECT COUNT(*) FROM Ingresso').fetchone()
    quantidade = resultado[0]
    return quantidade + 1

#TODO: Ver preço do ingresso
PRECO_INGRESSO = 100

@routes.post('/info_ingressos/criar_ingressos')
def criar_ingressos():
    if cronometro_expirado():
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

            eh_crianca = bool(item.get('eh_crianca', False))
            observacoes = item.get('observacoes')
            telefone = item.get('telefone')

            token = _gerar_token_unico(db)
            # Acredito não ser necessário. Ver TODO para mais detalhes
            novo_id = _proximo_id_ingresso(db)

            db.execute(
                '''
                INSERT INTO Ingresso (
                    nome, eh_crianca, observacoes, email_envio,
                    foi_pago, token_QR, utilizado, data_utilizado,
                    cod_aluno, cod_lugar, data_compra, telefone
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    nome,
                    eh_crianca,
                    observacoes,
                    email_envio,
                    1,          # foi_pago -> simulado como aprovado
                    token,
                    0,          # utilizado
                    None,       # data_utilizado
                    codigo_aluno,
                    cod_lugar,
                    datetime.now(),
                    telefone,
                )
            )

            db.execute(
                'UPDATE Lugares SET ocupado = 1 WHERE cod_lugar = ?',
                (cod_lugar,)
            )

            tokens_criados.append(token)

            if eh_crianca:
                a_pagar += PRECO_INGRESSO/2
            else:
                a_pagar += PRECO_INGRESSO

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
        return jsonify({'erro': f'Erro ao criar ingressos: {e}'}), 500

    session['tokens_criados'] = tokens_criados
    session['a_pagar'] = a_pagar
    # ======================================================================
    # ENVIO DOS EMAILS
    # feito DEPOIS do commit: se o email falhar, os ingressos já criados
    # não são perdidos — só registramos a falha pra tratar depois.
    # ======================================================================
    falhas_envio = []

    for token in tokens_criados:
        try:
            enviar_ingresso_por_email(token)
        except Exception as e:
            falhas_envio.append({'token': token, 'erro': str(e)})


    # Acredito ser melhor manter para pagamento
    #session.pop('lugares', None)
    #session.pop('codigo', None)

    resposta = {
        'sucesso': 'Ingressos criados com sucesso.',
        'tokens': tokens_criados,
    }

    if falhas_envio:
        resposta['aviso'] = (
            'Ingressos criados, mas houve falha ao enviar alguns emails.'
        )
        resposta['falhas_envio'] = falhas_envio

    return jsonify(resposta), 201


@routes.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    if request.method == 'POST':
        #Acredito ser melhor colocar mudanças do código do aluno e envio de email aqui
        pass
    lugares, a_pagar = session.get('lugares'), session.get('a_pagar')

    if not lugares:
        return jsonify({'erro': 'Nenhum lugar reservado na sessão.'}), 400
    if not a_pagar:
        return jsonify({'erro': 'Sem preço previsto para ser pago'}), 400

    return render_template(
        'ingressos/pagamento.html',
        luagres=lugares,
        a_pagar=a_pagar
    )