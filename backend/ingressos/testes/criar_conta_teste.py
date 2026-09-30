"""
Cria uma conta de teste (comprador) na Mercado Pago via API e imprime o
e-mail gerado. Rode uma vez, guarde o e-mail e senha que aparecerem.

Uso:
    python criar_conta_teste.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]  # seu token de TESTE

resposta = requests.post(
    "https://api.mercadopago.com/users/test_user",
    headers={
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"site_id": "MLB"},  # MLB = Brasil, apesar do prefixo
)

dados = resposta.json()

print("Status:", resposta.status_code)
print("E-mail:", dados.get("email"))
print("Senha:", dados.get("password"))
print("ID:", dados.get("id"))
print()
print("Resposta completa:", dados)