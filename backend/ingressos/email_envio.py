import os
import smtplib

from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv(
    "MAIL_DEFAULT_SENDER",
    MAIL_USERNAME
)
MAIL_SENDER_NAME = os.getenv(
    "MEIL_SENDER_NAME",
    "Bistrô 2026"
)


def enviar_email(
    destinatario,
    assunto,
    mensagem,
    anexo=None,
):
    """
    Envia um email utilizando o SMTP do Gmail.

    destinatario:
        Email que receberá a mensagem.

    assunto:
        Assunto do email.

    mensagem:
        Texto do email.

    anexo:
        Caminho do arquivo que será anexado.
    """

    if not MAIL_SERVER:
        raise RuntimeError(
            "MAIL_SERVER não foi configurado."
        )

    if not MAIL_USERNAME:
        raise RuntimeError(
            "MAIL_USERNAME não foi configurado."
        )

    if not MAIL_PASSWORD:
        raise RuntimeError(
            "MAIL_PASSWORD não foi configurado."
        )

    msg = EmailMessage()

    msg["From"] = formataddr((MAIL_SENDER_NAME, MAIL_DEFAULT_SENDER))
    msg["To"] = destinatario
    msg["Subject"] = assunto

    msg.set_content(mensagem)

    # ========================================================
    # ANEXO
    # ========================================================

    if anexo is not None:

        lista_anexos = anexo if isinstance(anexo, (list, tuple)) else [anexo]

        for item in lista_anexos:

            caminho = Path(anexo)

            if not caminho.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}"
                )

            with open(caminho, "rb") as arquivo:
                dados = arquivo.read()

            msg.add_attachment(
                dados,
                maintype="application",
                subtype="pdf",
                filename=caminho.name,
            )

    # ========================================================
    # CONEXÃO COM O GMAIL
    # ========================================================

    #print("Conectando ao servidor SMTP...")

    try:

        with smtplib.SMTP_SSL(
            MAIL_SERVER,
            MAIL_PORT,
            #timeout=15
        ) as servidor:

            #print("Conectado ao servidor SMTP.")

            #print("Fazendo login...")

            servidor.login(
                MAIL_USERNAME,
                MAIL_PASSWORD
            )

            #print("Login realizado.")

            #print("Enviando email...")

            servidor.send_message(msg)

            #print("Email enviado pelo servidor SMTP.")

    except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                "Falha na autenticação SMTP. Verifique MAIL_USERNAME e "
                "MAIL_PASSWORD (para Gmail, use uma 'senha de app', não a "
                "senha normal da conta)."
        ) from e

    except smtplib.SMTPConnectError as e:
        raise RuntimeError(
            f"Não foi possível conectar ao servidor {MAIL_SERVER}:{MAIL_PORT}."
        ) from e

    except smtplib.SMTPRecipientsRefused as e:
        raise RuntimeError(
            f"O destinatário foi recusado pelo servidor: {destinatario}."
        ) from e

    except TimeoutError as e:
        raise RuntimeError(
            "Tempo limite excedido ao conectar/enviar o email."
        ) from e

    except smtplib.SMTPException as e:
        raise RuntimeError(
            f"Erro ao enviar email: {e}"
        ) from e
