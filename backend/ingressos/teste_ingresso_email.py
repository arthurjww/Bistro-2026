"""
Script de teste manual: cria um ingresso fake no banco (já marcado
como pago) e testa a geração do PDF + envio por email de ponta a ponta.

Rodar a partir da raiz do projeto:
    TODO: python -m backend.ingressos.teste_ingresso_email
"""

from datetime import datetime

from backend import app
from backend.banco_de_dados import get_db
<<<<<<< HEAD
from backend.ingressos.gerador_pdf import enviar_ingresso_por_email 


EMAIL_TESTE = "gmatte1@ucs.br"  # TODO: troque pro seu email de teste
=======
from backend.ingressos.gerador_pdf import enviar_ingresso_por_email


EMAIL_TESTE = ""  # TODO: troque pro seu email de teste
>>>>>>> fdf8986a4083e4a3934853c246602ceb6203b48b
TOKEN_TESTE = "TEST01"


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

    # Remove qualquer ingresso de teste anterior com o mesmo token,
    # já que o id agora é autoincrementado (não dá mais pra usar
    # INSERT OR REPLACE direto pelo id)
    db.execute(
        "DELETE FROM Ingresso WHERE token_QR = ?",
        (TOKEN_TESTE,)
    )

    # Ingresso de teste, já pago
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
            datetime.now(),
            "",
        )
    )

    db.commit()
    print("Dados de teste prontos.")


def limpar_dados_teste(db): #TODO : para nao deixar os dados de testes salvos no banco
    print("Limpando dados de teste do banco...")
    db.execute("DELETE FROM Ingresso WHERE token_QR = ?", (TOKEN_TESTE,))
    db.execute("DELETE FROM Lugares WHERE cod_lugar = ?", ("T1",))
    db.execute("DELETE FROM Aluno WHERE cod_aluno = ?", ("TESTE1",))
    db.commit()
    print("Dados de teste removidos.")


if __name__ == "__main__":
    with app.app_context():
        db = get_db()

        preparar_dados_teste(db)

        try:
            print("Testando geração de PDF + envio de email...")
            enviar_ingresso_por_email(TOKEN_TESTE)
            print("Email com PDF enviado com sucesso!")

        except Exception as e:
            print(f"Falha no teste: {e}")

        finally:
<<<<<<< HEAD
            limpar_dados_teste(db)
=======
            limpar_dados_teste(db)
            
>>>>>>> fdf8986a4083e4a3934853c246602ceb6203b48b
