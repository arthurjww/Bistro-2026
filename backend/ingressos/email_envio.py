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
    "MAIL_SENDER_NAME",
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
        Pode ser:
        - Caminho (str ou Path) de um arquivo no disco.
        - Tupla (nome_arquivo, bytes_ou_BytesIO) para anexar
          conteúdo gerado em memória, sem precisar salvar em disco.
        - Lista contendo qualquer combinação dos formatos acima,
          para enviar múltiplos anexos.
        - None se não houver anexo.
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
    # ANEXO(S)
    # ========================================================

    if anexo is not None:

        # sempre exige uma lista para múltiplos anexos, evitando
        # ambiguidade entre "uma tupla" e "uma lista de 2 anexos"
        lista_anexos = anexo if isinstance(anexo, list) else [anexo]

        for item in lista_anexos:

            if isinstance(item, (str, Path)):
                caminho = Path(item)

                if not caminho.exists():
                    raise FileNotFoundError(
                        f"Arquivo não encontrado: {caminho}"
                    )

                with open(caminho, "rb") as arquivo:
                    dados = arquivo.read()

                filename = caminho.name

            elif isinstance(item, tuple) and len(item) == 2:
                filename, conteudo = item

                # aceita BytesIO ou bytes puro
                dados = (
                    conteudo.getvalue()
                    if hasattr(conteudo, "getvalue")
                    else conteudo
                )

            else:
                raise TypeError(
                    "Anexo inválido. Use um caminho de arquivo (str/Path) "
                    "ou uma tupla (nome_arquivo, bytes/BytesIO)."
                )

            msg.add_attachment(
                dados,
                maintype="application",
                subtype="pdf",
                filename=filename,
            )

    # ========================================================
    # CONEXÃO COM O GMAIL
    # ========================================================


    try:
        with smtplib.SMTP_SSL(
            MAIL_SERVER,
            MAIL_PORT,
            timeout=15
        ) as servidor:


            servidor.login(
                MAIL_USERNAME,
                MAIL_PASSWORD
            )
            
            servidor.send_message(msg)

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