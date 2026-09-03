from backend.banco_de_dados import get_db
from backend.ingressos.email_envio import enviar_email

from pathlib import Path
import secrets


file = Path(__file__).resolve().parents[2] / 'nomes_emails.csv'


CHARS_TOKEN = 'ACDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz234679'


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
                nome = linha.strip().split(';')[0]

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
                if nome != 'Guilherme Terres Munaretto da Costa':
                    continue

                pk = _gerar_token_unico(db)

                db.execute(
                '''
                    INSERT INTO Aluno
                    VALUES (?, ?, ?)
                ''', (pk, nome, 2)
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
                nome, email = linha.strip().split(';')
                # TODO: TESTE
                if nome != 'Guilherme Terres Munaretto da Costa':
                    continue
                pk = db.execute(
                    '''
                    SELECT cod_aluno
                    FROM Aluno
                    WHERE nome_aluno = ?
                    ''', (nome,)
                ).fetchone()

                msg = f'''{nome}
                Abaixo está o seu código para ser utilizado para a compra dos ingresso no Bistrot 2026 Sinestesia
                {pk["cod_aluno"]}'''
                enviar_email(email, 'Código para compra de ingressos', msg)
            print('enviado')
    except FileNotFoundError as e:
        print(e)