from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['cod_aluno'] = 'ALU123'  # simula aluno já "logado"

    resp = client.post('/api/lugares/A1/escolher')
    print(resp.status_code, resp.get_json())

    resp = client.post('/api/lugares/A1/confirmar')
    print(resp.status_code, resp.get_json())