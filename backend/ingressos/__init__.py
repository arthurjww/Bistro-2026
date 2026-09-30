import os
import mercadopago

# Inicializa o SDK do Mercado Pago utilizando a chave do .env
access_token = os.getenv("MP_ACCESS_TOKEN", "")
sdk = mercadopago.SDK(access_token)