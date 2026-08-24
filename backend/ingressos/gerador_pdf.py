import sqlite3
import qrcode
import io
import base64
from flask import Blueprint, request, render_template_string, send_file
from xhtml2pdf import pisa
from ..banco_de_dados import get_db

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
  db.row_factory = (
    sqlite3.Row
  )
  cursor = db.cursor()

  cursor.execute(
    """
        SELECT
            nome,
            email_envio AS email,
            data_compra,
            token_QR AS token,
            cod_lugar,
            CASE WHEN eh_crianca = 1 THEN 'Criança' ELSE 'Adulto' END AS tipo
        FROM Ingresso
        WHERE token_QR = ? AND foi_pago = 1
    """,
      (token,),
  )

  return cursor.fetchone()

@gerador_pdf.route('/generate-pdf', methods=['GET'])
def generate_pdf():
    token = request.args.get('token')

    if not token:
        return "Parâmetro 'token' ausente na requisição.", 400

    # 1. Busca no Banco de Dados (Apenas se o pagamento foi confirmado)
    ingresso = buscar_ingresso_pago(token)

    if not ingresso:
        return "Ingresso não encontrado ou pagamento ainda não aprovado.", 404

    # 2. O QR Code armazena o Token para ser lido na portaria do evento
    qr_img = qrcode.make(ingresso['token'])
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    # 3. Renderização do HTML
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

    # 4. Geração do PDF em memória
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_rendered, dest=pdf_buffer)

    if pisa_status.err:
        return "Erro ao gerar o PDF", 500

    pdf_buffer.seek(0)

    nome_arquivo = f"Ingresso_Sinestesia_{ingresso['nome'].replace(' ', '_')}.pdf"
    print("teste email")
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )