"""
Teste automatizado do fluxo completo de criação de ingressos, simulando
as requisições que o frontend fará no futuro (via Flask test_client):

1. Simula um lugar já reservado na sessão
   (normalmente isso seria feito pela rota de reserva de mesas)
2. Confirma o código do aluno
3. Cria os ingressos -> grava no banco
4. Processa pagamento -> gera PDF, envia email

Rodar a partir da raiz do projeto:
    python -m backend.ingressos.testes.teste_cliente
"""

from backend import app
from backend.mapa_mesas.banco_de_dados import get_db


CODIGO_ALUNO_TESTE = "TOK123"
LUGAR_TESTE = "T2"
EMAIL_TESTE = ""  # troque pro seu email de teste


def preparar_dados_teste(db):
    print("Preparando dados de teste no banco...")

    db.execute(
        '''
        INSERT OR REPLACE INTO Aluno (cod_aluno, nome_aluno, usos_restantes)
        VALUES (?, ?, ?)
        ''',
        (CODIGO_ALUNO_TESTE, "Aluno Fluxo Completo", 5)
    )

    db.execute(
        '''
        INSERT OR REPLACE INTO Lugares (cod_lugar, cod_aluno, mesa, ocupado, cronometro_reservado)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (LUGAR_TESTE, CODIGO_ALUNO_TESTE, "B", 0, None)
    )

    db.commit()
    print("Dados de teste prontos.")


def limpar_dados_teste(db):
    print("Limpando dados de teste do banco...")
    db.execute("DELETE FROM Ingresso WHERE cod_lugar = ?", (LUGAR_TESTE,))
    db.execute("DELETE FROM Lugares WHERE cod_lugar = ?", (LUGAR_TESTE,))
    db.execute("DELETE FROM Aluno WHERE cod_aluno = ?", (CODIGO_ALUNO_TESTE,))
    db.commit()
    print("Dados de teste removidos.")


if __name__ == "__main__":

    with app.app_context():
        preparar_dados_teste(get_db())

    client = app.test_client()

    try:
        # 1. Simula um lugar já reservado na sessão
        with client.session_transaction() as sess:
            sess['lugares'] = [LUGAR_TESTE]

        # 2. Confirma o código do aluno
        print("\n--- Confirmando código do aluno ---")
        resposta = client.post(
            '/info_ingressos/confirmar_codigo',
            json={'cronometro': 60, 'codigo': CODIGO_ALUNO_TESTE}
        )
        print("Status:", resposta.status_code)
        print("Body:", resposta.get_json())

        if resposta.status_code != 200:
            raise RuntimeError("Falha ao confirmar código, abortando teste.")

        # 3. Cria os ingressos (salva no banco)
        print("\n--- Criando ingressos ---")
        resposta = client.post(
            '/info_ingressos/criar_ingressos',
            json={
                'ingressos': [
                    {
                        'nome': 'Convidado Fluxo Completo',
                        'eh_crianca': False,
                        'email_envio': EMAIL_TESTE,
                        'telefone': '',
                        'observacoes': 'teste automatizado do fluxo completo',
                    }
                ]
            }
        )
        print("Status:", resposta.status_code)
        print("Body:", resposta.get_json())

        if resposta.status_code != 201:
            raise RuntimeError("Falha ao criar ingressos, abortando teste.")

        # 4. Simula o pagamento (gera PDF + envia email)
        print("\n--- Processando pagamento e enviando email ---")
        resposta = client.post('/pagamento')
        print("Status:", resposta.status_code)
        print("Body:", resposta.get_json())

    finally:
        with app.app_context():
            limpar_dados_teste(get_db())