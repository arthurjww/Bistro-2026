import base64
import io
import os
import re
import unicodedata
import qrcode
from datetime import datetime
from flask import Blueprint, request, render_template, send_file, url_for, session
from xhtml2pdf import pisa
from ..banco_de_dados import get_db
from .email_envio import enviar_email

gerador_pdf = Blueprint('gerador_pdf', __name__)

# PIN simples pra proteger "Confirmar entrada" (só o staff na portaria sabe).
# Independente de qualquer login de admin que já exista no projeto.
STAFF_PIN = os.environ.get('STAFF_PIN', '')

def _gerar_nome_arquivo(nome):
    """Sanitiza o nome do titular para um formato seguro em SO e HTTP."""
    nome_ascii = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    nome_limpo = re.sub(r'[^\w\s-]', '', nome_ascii)
    nome_limpo = re.sub(r'[\s-]+', '_', nome_limpo).strip('_')
    nome_final = nome_limpo if nome_limpo else "Visitante"
    return f"Ingresso_Sinestesia_{nome_final}.pdf"

def _gerar_pdf_bytes(ingresso):
    """Gera o PDF do ingresso em memória e retorna um BytesIO."""

    url_validacao = (
        "https://mesas.sinestesiabistro.com.br/validar"
        f"?token={ingresso['token']}"
    )
    qr_img = qrcode.make(url_validacao)

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    html_rendered = render_template(
        'ingressos/ingresso.html',
        nome=ingresso['nome'],
        tipo=ingresso['tipo'],
        email=ingresso['email'],
        data_compra=ingresso['data_compra'],
        token=ingresso['token'],
        lugar=ingresso['cod_lugar'],  # Exibe o assento/mesa
        qr_code=qr_base64,
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_rendered, dest=pdf_buffer)

    if pisa_status.err:
        raise RuntimeError("Erro ao gerar o PDF do ingresso.")

    pdf_buffer.seek(0)
    return pdf_buffer

def buscar_ingresso_pago(token):
    db = get_db()
    cursor = db.cursor()
    try:
      cursor.execute(
        """
            SELECT
                i.nome,
                i.email_envio AS email,
                i.data_compra,
                i.token_QR AS token,
                i.utilizado,
                i.data_utilizado,
                r.cod_lugar,
                r.dia_bistro,
                CASE
                    WHEN i.tipo_ingresso = 0 THEN 'Gratuito'
                    WHEN i.tipo_ingresso = 1 THEN 'Meia'
                    ELSE 'Inteira'
                END AS tipo
            FROM Ingresso i
            INNER JOIN Reserva r
                ON i.cod_reserva = r.cod_reserva
            WHERE i.token_QR = ? AND i.foi_pago = 1
        """,
          (token,),
        )
      return cursor.fetchone()
    finally:
        cursor.close()

def gerar_pdf_ingresso(token):
    """
    Busca o ingresso pago e gera o PDF em memória.

    Retorna (pdf_buffer, nome_arquivo), ou (None, None) se o
    ingresso não existir ou não estiver pago.
    """
    ingresso = buscar_ingresso_pago(token)

    if not ingresso:
        return None, None

    pdf_buffer = _gerar_pdf_bytes(ingresso)
    nome_arquivo =_gerar_nome_arquivo(ingresso['nome'])

    return pdf_buffer, nome_arquivo


def enviar_ingresso_por_email(token):
    """
    Gera o PDF do ingresso e envia por email para o titular.

    Levanta ValueError se o ingresso não existir ou não estiver pago.
    Propaga RuntimeError se o envio de email falhar (SMTP).
    """
    ingresso = buscar_ingresso_pago(token)

    if not ingresso:
        raise ValueError("Ingresso não encontrado ou pagamento não aprovado.")

    pdf_buffer = _gerar_pdf_bytes(ingresso)
    nome_arquivo = _gerar_nome_arquivo(ingresso['nome'])

    enviar_email(
        destinatario=ingresso['email'],
        assunto="Seu ingresso - Sinestesia 2026",

        mensagem_texto=(
            f"Olá, {ingresso['nome']}!\n\n"
            "Seu ingresso para o Sinestesia 2026 está confirmado. "
            "Ele segue em anexo neste email, em PDF.\n\n"
            "Apresente o QR code do ingresso na entrada do evento.\n\n"
            "Até lá!\n"
            "Equipe Sinestesia"
        ),

        mensagem_html=None,

        anexo=[(nome_arquivo, pdf_buffer)],
    )


@gerador_pdf.route('/generate-pdf', methods=['GET'])
def generate_pdf():
    token = request.args.get('token')

    if not token:
        return "Parâmetro 'token' ausente na requisição.", 400

    pdf_buffer, nome_arquivo = gerar_pdf_ingresso(token)

    if pdf_buffer is None:
        return "Ingresso não encontrado ou pagamento ainda não aprovado.", 404

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )

@gerador_pdf.route('/validar', methods=['GET'])
def validar_ingresso():
  """
  Só CONSULTA o ingresso — nunca marca como utilizado aqui. O convidado
  pode abrir o QR em casa quantas vezes quiser sem queimar a entrada.
  A confirmação de verdade acontece em /validar/confirmar, na portaria.
  """

  token = request.args.get('token')

  if not token:
    return render_template('ingressos/validacao.html', status='invalido'), 400

  ingresso = buscar_ingresso_pago(token)

  if not ingresso:
    return render_template('ingressos/validacao.html', status='invalido'), 404

  if ingresso['utilizado']:
    return render_template(
      'ingressos/validacao.html',
      status='ja_utilizado',
      nome=ingresso['nome'],
      lugar=ingresso['cod_lugar'],
      tipo=ingresso['tipo'],
      data_utilizado=ingresso['data_utilizado'],
    )

  return render_template(
    'ingressos/validacao.html',
    status='valido',
    token=token,
    staff_autenticado=bool(session.get('staff_autenticado')),
    nome=ingresso['nome'],
    lugar=ingresso['cod_lugar'],
    tipo=ingresso['tipo'],
    data_compra=ingresso['data_compra'],
  )


@gerador_pdf.route('/validar/confirmar', methods=['POST'])
def confirmar_entrada():
  """
  Ação separada, só pra portaria: exige o PIN do staff (uma vez por
  dispositivo/sessão) e só então marca o ingresso como utilizado.
  """

  token = request.form.get('token')
  pin = request.form.get('pin', '')

  if not token:
    return render_template('ingressos/validacao.html', status='invalido'), 400

  if not session.get('staff_autenticado'):
    if not STAFF_PIN or pin != STAFF_PIN:
      ingresso = buscar_ingresso_pago(token)
      return render_template(
        'ingressos/validacao.html',
        status='valido',
        token=token,
        staff_autenticado=False,
        erro_pin='PIN incorreto.',
        nome=ingresso['nome'] if ingresso else None,
        lugar=ingresso['cod_lugar'] if ingresso else None,
        tipo=ingresso['tipo'] if ingresso else None,
        data_compra=ingresso['data_compra'] if ingresso else None,
      ), 403
    session['staff_autenticado'] = True

  ingresso = buscar_ingresso_pago(token)

  if not ingresso:
    return render_template('ingressos/validacao.html', status='invalido'), 404

  if ingresso['utilizado']:
    return render_template(
      'ingressos/validacao.html',
      status='ja_utilizado',
      nome=ingresso['nome'],
      lugar=ingresso['cod_lugar'],
      tipo=ingresso['tipo'],
      data_utilizado=ingresso['data_utilizado'],
    )

  db = get_db()
  db.execute(
    'UPDATE Ingresso SET utilizado = 1, data_utilizado = ? WHERE token_QR = ?',
    (datetime.now(), token)
  )
  db.commit()

  return render_template(
    'ingressos/validacao.html',
    status='confirmado',
    nome=ingresso['nome'],
    lugar=ingresso['cod_lugar'],
    tipo=ingresso['tipo'],
    data_compra=ingresso['data_compra'],
  )
