from backend import app
from backend.banco_de_dados import get_db
from backend.ingressos.gerador_pdf import enviar_ingresso_por_email


with app.app_context():

    db = get_db()

    # =========================
    # 1. Criar aluno de teste
    # =========================

    db.execute("""
        INSERT OR IGNORE INTO Aluno
        (cod_aluno, nome_aluno, usos_restantes)
        VALUES (?, ?, ?)
    """, (
        "TEST01",
        "Matté Teste",
        0
    ))

    # =========================
    # 2. Criar lugar de teste
    # =========================

    db.execute("""
        INSERT OR IGNORE INTO Lugares
        (cod_lugar, salao)
        VALUES (?, ?)
    """, (
        "T01",
        1
    ))

    # =========================
    # 3. Criar reserva de teste
    # =========================

    db.execute("""
        INSERT OR IGNORE INTO Reserva
        (cod_lugar, cod_aluno, dia_bistro, ocupado)
        VALUES (?, ?, ?, ?)
    """, (
        "T01",
        "TEST01",
        "2026-10-29",
        1
    ))

    # Buscar a reserva existente
    reserva = db.execute("""
        SELECT cod_reserva
        FROM Reserva
        WHERE cod_lugar = ?
        AND cod_aluno = ?
        AND dia_bistro = ?
    """, (
        "T01",
        "TEST01",
        "2026-10-29"
    )).fetchone()

    cod_reserva = reserva["cod_reserva"]

    # =========================
    # 4. Criar ingresso de teste
    # =========================

    token = "ABC123"

    db.execute("""
        INSERT OR IGNORE INTO Ingresso
        (
            nome,
            tipo_ingresso,
            email_envio,
            foi_pago,
            token_QR,
            cod_aluno,
            cod_reserva,
            data_compra,
            telefone,
            valor_pago
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Matté Teste",
        2,
        "", #TODO: preencher com email de teste, usar token com foi_pago = 1 do teste.db
        1,
        token,
        "TEST01",
        cod_reserva,
        "2026-10-07 21:00:00",
        "54999999999",
        10.00
    ))

    db.commit()

    # =========================
    # 5. Testar envio
    # =========================

    print(f"Token: {token}")
    print("Enviando e-mail...")

    try:
        with app.test_request_context():
            enviar_ingresso_por_email(token)

        print("✅ E-MAIL ENVIADO COM SUCESSO!")

    except Exception as e:
        print("❌ ERRO AO ENVIAR E-MAIL:")
        print(type(e).__name__)
        print(e)