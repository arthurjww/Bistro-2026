import os
import secrets
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from dotenv import load_dotenv
from flask import render_template

from backend.banco_de_dados import get_db

load_dotenv()

# Vai dar erro caso não encontre a env var, e isso é proposital
CSV_PATH = Path(__file__).resolve().parents[2] / os.getenv('CSV_ALUNOS', 'não_encontrada.erro')
CHARS_TOKEN = 'ACDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz234679'

MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
MAIL_SENDER_NAME = os.getenv('MAIL_SENDER_NAME', 'Bistrô 2026')

MENSAGEM_TEXTO = '''
Olá, {nome}.

Segue o código abaixo para seus convidados no Bistrô 2026 Sinestesia.

Código: {codigo}

Você pode usá-lo até {usos} vezes.

Abaixo seguem as instruções:

- Este código é usado para validar a compra dos ingressos.

- Apenas o compartilhe com pessoas de confiança.

- Após a escolha do código e dos lugares, você terá 30 minutos* para escrever as informações dos ingressos e pagar.
  * Esses 30 minutos serão resetados após avançar para o pagamento e ao gerar o PIX.

- Caso necessário, é possível comprar ingressos com o mesmo código em diferentes sessões.

- Qualquer dúvida, entre em contato conosco:
  Site: sinestesiabistro.com.br
  Telefone: +55 (54) 99112-1192
  E-mail: sacsinestesiabistro@gmail.com
'''.strip()


def _gerar_token_unico(db, tokens_em_uso):
    """Gera um token de 6 caracteres único, checando o banco e a memória atual."""
    while True:
        token = ''.join(secrets.choice(CHARS_TOKEN) for _ in range(6))

        if token in tokens_em_uso:
            continue

        existe = db.execute('SELECT 1 FROM Aluno WHERE cod_aluno = ?', (token,)).fetchone()
        if not existe:
            tokens_em_uso.add(token)
            return token


def _ler_csv():
    """Lê o arquivo CSV e retorna uma lista de tuplas com os dados."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f'Arquivo não encontrado: {CSV_PATH}')

    dados = []
    with CSV_PATH.open('r', encoding='utf-8') as f:
        for linha in f:
            partes = linha.strip().split(',')
            if len(partes) == 3:
                nome, email, quant = [p.strip() for p in partes]
                dados.append((nome, email, int(quant)))
    return dados


def criar_alunos():
    """Lê os alunos do CSV e cadastra no banco em lote (Bulk Insert)."""
    db = get_db()

    try:
        alunos_csv = _ler_csv()

        nomes_bd = db.execute('SELECT nome_aluno FROM Aluno').fetchall()
        nomes_existentes = {row['nome_aluno'] for row in nomes_bd}

        novos_alunos = []
        tokens_em_uso = set()

        for nome, _, quant in alunos_csv:
            if nome in nomes_existentes:
                continue

            pk = _gerar_token_unico(db, tokens_em_uso)
            novos_alunos.append((pk, nome, quant))

        if novos_alunos:
            db.executemany(
                'INSERT INTO Aluno (cod_aluno, nome_aluno, usos_restantes) VALUES (?, ?, ?)',
                novos_alunos
            )
            db.commit()

        print(f'Criação finalizada: {len(novos_alunos)} novos alunos adicionados.')

    except Exception as e:
        print(f'Erro ao criar alunos: {e}')


def _worker_enviar_lote(lote_mensagens):
    """Função executada pelas threads para enviar um lote de emails na mesma conexão SMTP."""
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=15) as servidor:
            servidor.login(MAIL_USERNAME, MAIL_PASSWORD)
            for msg in lote_mensagens:
                servidor.send_message(msg)
    except Exception as e:
        print(f'Erro ao enviar lote de emails: {e}')


def enviar_cod():
    """Constrói as mensagens e dispara os e-mails de forma paralela e otimizada."""
    if not all([MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD]):
        raise RuntimeError('Configurações de e-mail ausentes.')

    db = get_db()

    try:
        alunos_csv = _ler_csv()

        alunos_bd = db.execute('SELECT cod_aluno, nome_aluno, usos_restantes FROM Aluno').fetchall()
        dict_alunos = {aluno['nome_aluno']: aluno for aluno in alunos_bd}

        mensagens_para_enviar = []

        for nome, email, quant in alunos_csv:
            aluno = dict_alunos.get(nome)

            if not aluno:
                print(f'Aviso: Aluno {nome} não encontrado no banco de dados. Pulando.')
                continue

            msg_texto = MENSAGEM_TEXTO.format(
                nome=nome,
                codigo=aluno['cod_aluno'],
                usos=aluno['usos_restantes']
            )

            msg_html = render_template(
                'ingressos/codigo_aluno.html',
                nome=nome,
                codigo=aluno['cod_aluno'],
                usos=aluno['usos_restantes']
            )

            msg = EmailMessage()
            msg['From'] = formataddr((MAIL_SENDER_NAME, MAIL_DEFAULT_SENDER))
            msg['To'] = email
            msg['Subject'] = 'Código para compra de ingressos'
            msg.set_content(msg_texto)
            msg.add_alternative(msg_html, subtype='html')

            mensagens_para_enviar.append(msg)

        if not mensagens_para_enviar:
            print('Nenhuma mensagem para enviar.')
            return

        tamanho_lote = 30
        lotes = [
            mensagens_para_enviar[i:i + tamanho_lote]
            for i in range(0, len(mensagens_para_enviar), tamanho_lote)
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(_worker_enviar_lote, lotes)

        print(f'{len(mensagens_para_enviar)} e-mails foram processados com sucesso.')

    except Exception as e:
        print(f'Erro ao processar envios: {e}')


def main(choice):
    if choice not in (1, 2, 3):
        return

    if choice == 1 or choice == 3:
        criar_alunos()

    if choice == 2 or choice == 3:
        enviar_cod()


CHOICE = 0


if __name__ == '__main__':
    # Qualquer coisa que não é 1, 2, ou 3 - não executa o programa
    # 1 - só cria os alunos
    # 2 - só envia os emails
    # 3 - cria os alunos e envia os emails
    main(CHOICE)