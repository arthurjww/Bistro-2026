import qrcode
import io
import base64
from flask import Blueprint, request, render_template_string, send_file, url_for
from xhtml2pdf import pisa
from ..mapa_mesas.banco_de_dados import get_db
from .email_envio import enviar_email

gerador_pdf = Blueprint('gerador_pdf', __name__)

#Editar HTML
HTML_INGRESSO = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page {
      size: A4 portrait;
      margin: 20px;
    }
    body {
      font-family: Helvetica, Arial, sans-serif;
      background-color: #581418;
      color: #FAF2DF;
      padding: 20px;
    }
    .ticket {
      width: 100%;
      background-color: #3b0d10;
      border: 2px solid #CFA86E;
      border-radius: 8px;
      border-collapse: collapse;
    }
    .main-info {
      width: 68%;
      padding: 25px;
      vertical-align: top;
      border-right: 2px dashed #CFA86E;
    }
    .stub-info {
      width: 32%;
      padding: 20px;
      vertical-align: middle;
      text-align: center;
      background-color: #2b090b;
    }
    .brand-title {
      font-size: 24px;
      font-weight: bold;
      letter-spacing: 4px;
      color: #FAF2DF;
      text-transform: uppercase;
    }
    .brand-subtitle {
      font-size: 11px;
      letter-spacing: 2px;
      color: #CFA86E;
      margin-top: 4px;
      font-style: italic;
    }
    .divider {
      border-bottom: 1px dashed #CFA86E;
      margin: 15px 0;
    }
    .label {
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #CFA86E;
      margin-top: 10px;
      margin-bottom: 2px;
    }
    .value {
      font-size: 13px;
      font-weight: bold;
      color: #FAF2DF;
    }
    .badge {
      background-color: #CFA86E;
      color: #581418;
      font-weight: bold;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .qr-code-img {
      width: 110px;
      height: 110px;
      border: 2px solid #CFA86E;
      border-radius: 6px;
      background-color: #FFFFFF;
      padding: 4px;
      margin-bottom: 8px;
    }
    .token-text {
      font-family: monospace;
      font-size: 8px;
      color: #CFA86E;
      word-wrap: break-word;
    }
  </style>
</head>
<body>
  <table class="ticket">
    <tr>
      <td class="main-info">
        <div class="brand-title">SINESTESIA</div>
        <div class="brand-subtitle">gastronomia em harmonia</div>

        <div class="divider"></div>

        <table width="100%">
          <tr>
            <td width="60%">
              <div class="label">Titular do Ingresso</div>
              <div class="value">{{ nome }}</div>
            </td>
            <td width="40%">
              <div class="label">Tipo</div>
              <div class="value"><span class="badge">{{ tipo }}</span></div>
            </td>
          </tr>
          <tr>
            <td width="60%">
              <div class="label">E-mail</div>
              <div class="value">{{ email }}</div>
            </td>
            <td width="40%">
              <div class="label">Data de Compra</div>
              <div class="value">{{ data_compra }}</div>
            </td>
          </tr>
        </table>
      </td>

      <td class="stub-info">
        <img src="data:image/png;base64,{{ qr_code }}" class="qr-code-img" />
        <div class="label">Validação</div>
        <div class="token-text">{{ token }}</div>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def buscar_ingresso_pago(token):
  db = get_db()
  cursor = db.cursor()

  cursor.execute(
    """
        SELECT
            nome,
            email_envio AS email,
            data_compra,
            token_QR AS token,
            cod_lugar,
            CASE
                WHEN tipo_ingresso = 0 THEN 'Gratuito'
                WHEN tipo_ingresso = 1 THEN 'Meia'
                ELSE 'Inteira'
            END AS tipo
        FROM Ingresso
        WHERE token_QR = ? AND foi_pago = 1
    """,
      (token,),
  )

  return cursor.fetchone()


def _gerar_pdf_bytes(ingresso):
    """Gera o PDF do ingresso em memória e retorna um BytesIO."""

    # O QR Code abre um site que diz se o ingresso é Válido ou Não.
    ip_servidor = "192.168.0.116:5000"
    url_validacao = f"http://{ip_servidor}/validar?token={ingresso['token']}"
    qr_img = qrcode.make(url_validacao) #TODO:REVER! 
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    html_rendered = render_template_string(
        HTML_INGRESSO,
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
    nome_arquivo = f"Ingresso_Sinestesia_{ingresso['nome'].replace(' ', '_')}.pdf"

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
    nome_arquivo = f"Ingresso_Sinestesia_{ingresso['nome'].replace(' ', '_')}.pdf"

    enviar_email(
        destinatario=ingresso['email'],
        assunto="Seu ingresso - Sinestesia 2026",
        mensagem=(
            f"Olá, {ingresso['nome']}!\n\n"
            "Seu ingresso para o Sinestesia 2026 está confirmado. "
            "Ele segue em anexo neste email, em PDF.\n\n"
            "Apresente o QR code do ingresso na entrada do evento.\n\n"
            "Até lá!\nEquipe Sinestesia"
        ),
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
  HTML_VALIDACAO = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Validação de Ingresso</title>
  <style>
    body { font-family: Arial, sans-serif; text-align: center; padding: 30px; background-color: #f4f4f9; }
    .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }
    .valido { color: #2e7d32; font-size: 26px; font-weight: bold; margin-bottom: 15px; }
    .invalido { color: #c62828; font-size: 26px; font-weight: bold; margin-bottom: 15px; }
    .info { text-align: left; font-size: 16px; line-height: 1.6; border-top: 1px solid #ddd; padding-top: 15px; }
  </style>
</head>
<body>
  <div class="card">
    {% if status == 'valido' %}
      <div class="valido">✅ Ingresso Válido!</div>
      <div class="info">
        <p><strong>Titular:</strong> {{ nome }}</p>
        <p><strong>Mesa/Lugar:</strong> {{ lugar }}</p>
        <p><strong>Tipo:</strong> {{ tipo }}</p>
        <p><strong>Data da Compra:</strong> {{ data_compra }}</p>
      </div>
    {% else %}
      <div class="invalido">❌ Ingresso Inválido</div>
      <p>Este ingresso não foi encontrado ou o pagamento não está aprovado.</p>
    {% endif %}
  </div>
</body>
</html>
"""

  token = request.args.get('token')

  if not token:
    return render_template_string(HTML_VALIDACAO, status='invalido'), 400

  ingresso = buscar_ingresso_pago(token)

  if not ingresso:
    return render_template_string(HTML_VALIDACAO, status='invalido'), 404

  return render_template_string(
    HTML_VALIDACAO,
    status='valido',
    nome=ingresso['nome'],
    lugar=ingresso['cod_lugar'],
    tipo=ingresso['tipo'],
    data_compra=ingresso['data_compra'],
  )