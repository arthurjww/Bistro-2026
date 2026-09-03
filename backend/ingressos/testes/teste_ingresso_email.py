"""
Script de teste manual: cria um ingresso fake no banco (já marcado
como pago) e testa a geração do PDF + envio por email de ponta a ponta.

Rodar a partir da raiz do projeto:
    python -m backend.ingressos.testes.teste_ingresso_email
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv  # Se estiver usando arquivo .env

from backend import app
from backend.banco_de_dados import get_db
from backend.ingressos.gerador_pdf import enviar_ingresso_por_email

# Carrega as variáveis do arquivo .env (caso use um)
load_dotenv()

EMAIL_TESTE = " "  # TODO: troque pro seu email de teste
TOKEN_TESTE = "TOK123"


def configurar_email_teste():
    """Garante que o app.config possui as credenciais de e-mail necessárias."""
    app.config.update(
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "t"),
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", "seu_email_remetente@gmail.com"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "sua_senha_de_app"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "seu_email_remetente@gmail.com")
    )


def preparar_dados_teste(db):
    print("Preparando dados de teste no banco...")

    # Aluno de teste
    db.execute(
        '''
        INSERT OR IGNORE INTO Aluno (cod_aluno, nome_aluno, usos_restantes)
        VALUES (?, ?, ?)
        ''',
        ("TESTE1", "Aluno de Teste", 5)
    )

    # Lugar de teste
    db.execute(
        '''
        INSERT OR IGNORE INTO Lugares (cod_lugar, cod_aluno, mesa, ocupado, cronometro_reservado)
        VALUES (?, ?, ?, ?, ?)
        ''',
        ("T1", "TESTE1", "A", 1, None)
    )

    # Remove qualquer ingresso de teste anterior com o mesmo token
    db.execute(
        "DELETE FROM Ingresso WHERE token_QR = ?",
        (TOKEN_TESTE,)
    )

    data_compra_str = datetime.now(timezone.utc).isoformat()

    # Ingresso de teste, já pago
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
            "Convidado de Teste",
            0,
            "Ingresso gerado só para teste de email/pdf",
            EMAIL_TESTE,
            1,
            TOKEN_TESTE,
            0,
            None,
            "TESTE1",
            "T1",
            data_compra_str,
            "",
            10.00,  # valor_pago para teste
        )
    )

    db.commit()
    print("Dados de teste prontos.")


def limpar_dados_teste(db):
    print("Limpando dados de teste do banco...")
    db.execute("DELETE FROM Ingresso WHERE token_QR = ?", (TOKEN_TESTE,))
    db.execute("DELETE FROM Lugares WHERE cod_lugar = ?", ("T1",))
    db.execute("DELETE FROM Aluno WHERE cod_aluno = ?", ("TESTE1",))
    db.commit()
    print("Dados de teste removidos.")


if __name__ == "__main__":
    with app.test_request_context():
        # Aplica as configurações do servidor de e-mail
        configurar_email_teste()

        db = get_db()
        preparar_dados_teste(db)

        try:
            print("Testando geração de PDF + envio de email...")
            enviar_ingresso_por_email(TOKEN_TESTE)
            print("Email com PDF enviado com sucesso!")

        except Exception as e:
            print(f"Falha no teste: {e}")

        #finally:
            #limpar_dados_teste(db)