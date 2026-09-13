from backend.banco_de_dados import get_db
from backend.ingressos.email_envio import enviar_email

from flask import render_template
from pathlib import Path
import secrets


file = Path(__file__).resolve().parents[2] / 'nomes_emails.csv'


CHARS_TOKEN = 'ACDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz234679'

mensagem_texto = '''
Olá, {nome}.

Segue o código abaixo para seus convidados no Bistrot 2026 Sinestesia.

Código: {codigo}

Você pode usá-lo até {usos} vezes.

Abaixo seguem as instruções:

- Este código é usado para validar a compra dos ingressos.
- Apenas o compartilhe com pessoas de confiança.
- Após a escolha do código e dos lugares, você terá 15 minutos para
  escrever as informações dos ingressos e pagar.
- Caso necessário, é possível comprar ingressos com o mesmo código
  em diferentes sessões.
- Qualquer dúvida, entre em contato conosco:
  +55 (54) 99999-9999.
'''.strip()

def _gerar_token_unico(db):
    """Gera um token de 6 caracteres alfanuméricos único na tabela alunos."""
    while True:
        token = ''.join(
            secrets.choice(CHARS_TOKEN)
            for _ in range(6)
        )

        existe = db.execute(
            'SELECT 1 FROM Aluno WHERE cod_aluno = ?',
            (token,)
        ).fetchone()

        if existe is None:
            return token


def criar_alunos():
    db = get_db()

    try:
        with file.open('r', encoding='utf-8') as f:
            for linha in f:
                nome, email, quant = linha.strip().split(',')

                igual = db.execute(
                    '''
                    SELECT *
                    FROM Aluno
                    WHERE nome_aluno = ?
                    ''', (nome,)
               ).fetchone()

                if igual is not None:
                    continue
                # TODO: TESTE
                if nome != 'Guilherme Matté':
                    continue

                pk = _gerar_token_unico(db)

                db.execute(
                '''
                    INSERT INTO Aluno
                    VALUES (?, ?, ?)
                ''', (pk, nome, int(quant))
                )
                print('criado')

        db.commit()

    except FileNotFoundError as e:
        print(e)


def enviar_cod():
    db = get_db()

    try:
        with file.open('r', encoding='utf-8') as f:
            for linha in f:
                nome, email, quant = linha.strip().split(',')
                # TODO: TESTE
                if nome != 'Guilherme Matté':
                    continue
                aluno = db.execute(
                    '''
                    SELECT *
                    FROM Aluno
                    WHERE nome_aluno = ?
                    ''', (nome,)
                ).fetchone()

                msg_texto = mensagem_texto.format(
                    nome=aluno['nome_aluno'],
                    codigo=aluno['cod_aluno'],
                    usos=aluno['usos_restantes']
                )
                msg_html = render_template(
                    'ingressos/codigo_aluno.html',
                    nome=aluno['nome_aluno'],
                    codigo=aluno['cod_aluno'],
                    usos=aluno['usos_restantes']
                )
                enviar_email(email, 'Código para compra de ingressos', msg_texto, msg_html)
            print('enviado')
    except FileNotFoundError as e:
        print(e)