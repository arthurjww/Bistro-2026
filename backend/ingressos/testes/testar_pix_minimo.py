import os
import uuid
from pathlib import Path
from typing import Any, Dict
import requests
from dotenv import load_dotenv


def carregar_env() -> None:
    """Localiza e carrega o arquivo .env localizado na raiz do projeto."""
    script_path = Path(__file__).resolve()
    env_file = next(
        (parent / ".env" for parent in [script_path] + list(script_path.parents) if (parent / ".env").is_file()),
        None
    )
    if env_file:
        load_dotenv(dotenv_path=env_file)
        print(f"📁 Arquivo .env carregado de: {env_file}")
    else:
        load_dotenv()


def gerar_pix_teste() -> None:
    carregar_env()

    access_token = os.environ.get("MP_ACCESS_TOKEN")
    if not access_token or not access_token.startswith("TEST-"):
        print("❌ ERRO: MP_ACCESS_TOKEN invalido ou ausente no .env. Deve iniciar com 'TEST-'.")
        return

    # E-mail neutro para evitar bloqueio de auto-pagamento (Erro 4390)
    email_comprador_sandbox = "comprador_homologacao_bistro2026@gmail.com"

    payload: Dict[str, Any] = {
        "transaction_amount": 50.00,
        "description": "Ingresso Bistro 2026 - Teste Pix",
        "payment_method_id": "pix",
        "external_reference": f"teste_{uuid.uuid4().hex}",
        "payer": {
            "email": email_comprador_sandbox,
            "first_name": "APRO",
            "last_name": "TEST",
            "identification": {
                "type": "CPF",
                "number": "19119119100"  # CPF generico de teste
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    print("🔄 Solicitando QR Code Pix via Payments API (/v1/payments)...")

    try:
        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=headers,
            json=payload,
            timeout=10
        )
    except requests.RequestException as exc:
        print(f"❌ Erro de conexao HTTP: {exc}")
        return

    print(f"\nStatus HTTP: {response.status_code}")
    dados = response.json()

    if response.status_code in (200, 201):
        status = dados.get("status")
        status_detail = dados.get("status_detail")
        pix_data = dados.get("point_of_interaction", {}).get("transaction_data", {})

        print(f"Status do Pagamento: {status}")
        print(f"Detalhe: {status_detail}")
        print("\n✅ QR CODE PIX GERADO COM SUCESSO!")
        print(f"Copia e Cola: {pix_data.get('qr_code')}")
        print(f"Ticket URL: {pix_data.get('ticket_url')}")
    else:
        print("\n❌ Falha na geracao do Pix:")
        print(dados)


if __name__ == "__main__":
    gerar_pix_teste()