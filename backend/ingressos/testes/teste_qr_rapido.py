"""
Cria um ingresso de teste já pago e gera o PDF com QR Code.

Rode com o Flask PARADO:

    python teste_qr_rapido.py

Depois:
1. Rode o Flask normalmente.
2. Abra o PDF gerado.
3. Escaneie o QR Code com a câmera do celular.
4. O celular abrirá a URL /validar?token=TSTQR1
"""

from datetime import datetime
from pathlib import Path

from backend import app
from backend.banco_de_dados import get_db
from backend.ingressos.gerador_pdf import gerar_pdf_ingresso


TOKEN_TESTE = "TSTQR1"


with app.app_context():

    db = get_db()

    # ==========================================================
    # 1. PEGAR OU CRIAR ALUNO
    # ==========================================================

    aluno = db.execute(
        "SELECT cod_aluno FROM Aluno LIMIT 1"
    ).fetchone()

    if aluno:
        cod_aluno = aluno["cod_aluno"]

    else:
        db.execute(
            """
            INSERT INTO Aluno (
                nome_aluno,
                usos_restantes
            )
            VALUES (?, ?)
            """,
            ("Aluno de Teste", 10)
        )

        cod_aluno = db.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

        db.commit()


    # ==========================================================
    # 2. REMOVER TESTE ANTERIOR
    # ==========================================================

    ingresso_antigo = db.execute(
        """
        SELECT cod_reserva
        FROM Ingresso
        WHERE token_QR = ?
        """,
        (TOKEN_TESTE,)
    ).fetchone()

    if ingresso_antigo:

        db.execute(
            """
            DELETE FROM Ingresso
            WHERE token_QR = ?
            """,
            (TOKEN_TESTE,)
        )

        db.execute(
            """
            DELETE FROM Reserva
            WHERE cod_reserva = ?
            """,
            (ingresso_antigo["cod_reserva"],)
        )

        db.commit()


    # ==========================================================
    # 3. CRIAR RESERVA
    # ==========================================================

    db.execute(
        """
        INSERT INTO Reserva (
            cod_lugar,
            cod_aluno,
            dia_bistro,
            ocupado,
            cronometro_reservado
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            9999,
            cod_aluno,
            "Teste",
            1,
            None
        )
    )

    cod_reserva = db.execute(
        "SELECT last_insert_rowid() AS id"
    ).fetchone()["id"]


    # ==========================================================
    # 4. CRIAR INGRESSO PAGO
    # ==========================================================

    db.execute(
        """
        INSERT INTO Ingresso (
            nome,
            tipo_ingresso,
            observacoes,
            email_envio,
            foi_pago,
            token_QR,
            utilizado,
            data_utilizado,
            cod_aluno,
            cod_reserva,
            data_compra,
            telefone,
            valor_pago
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Convidado de Teste",
            0,
            "teste QR Code",
            "teste@teste.com",
            1,
            TOKEN_TESTE,
            0,
            None,
            cod_aluno,
            cod_reserva,
            datetime.now(),
            "00000000000",
            0
        )
    )

    db.commit()


    # ==========================================================
    # 5. GERAR PDF COM QR CODE
    # ==========================================================

    print()
    print("Gerando ingresso com QR Code...")

    try:

        with app.test_request_context(
                base_url="https://snooper-creole-yeast.ngrok-free.dev"
        ):
            pdf_buffer, nome_arquivo = gerar_pdf_ingresso(TOKEN_TESTE)

        if pdf_buffer is None:
            raise Exception(
                "Não foi possível gerar o PDF. "
                "O ingresso não foi encontrado ou não está pago."
            )

        pasta_teste = Path(__file__).resolve().parent
        arquivo_pdf = pasta_teste / "ingresso_teste_qr.pdf"

        # pdf_buffer é um BytesIO
        arquivo_pdf.write_bytes(pdf_buffer.getvalue())

        print("✅ PDF criado com sucesso!")
        print(f"📄 Arquivo: {arquivo_pdf}")

    except Exception as e:

        print()
        print("❌ ERRO AO GERAR O PDF:")
        print(type(e).__name__)
        print(e)

        raise


    # ==========================================================
    # 6. URL DO QR CODE
    # ==========================================================

    url_teste = (
        "https://snooper-creole-yeast.ngrok-free.dev/"
        f"validar?token={TOKEN_TESTE}"
    )

    print()
    print("=" * 60)
    print("TESTE DO QR CODE")
    print("=" * 60)
    print()
    print(f"Token: {TOKEN_TESTE}")
    print()
    print("URL:")
    print(url_teste)
    print()
    print("1. Rode o Flask.")
    print("2. Abra o PDF gerado.")
    print("3. Aponte a câmera do celular para o QR Code.")
    print("4. Abra o link detectado.")
    print()
