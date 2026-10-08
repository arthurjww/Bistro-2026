import secrets

import click
from email_validator import EmailNotValidError, validate_email
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from ..banco_de_dados import get_db


@click.command("criar-admin")
@click.option("--nome", prompt="Nome do administrador")
@click.option("--email", prompt="E-mail do administrador")
@with_appcontext
def criar_admin(nome, email):
    """Cadastra um administrador e gera uma senha segura."""
    nome = nome.strip()

    if not nome:
        raise click.ClickException("O nome do administrador e obrigatorio.")

    if len(nome) > 50:
        raise click.ClickException("O nome pode ter no maximo 50 caracteres.")

    try:
        email = validate_email(
            email.strip(),
            check_deliverability=False
        ).normalized.lower()
    except EmailNotValidError as erro:
        raise click.ClickException(f"E-mail invalido: {erro}") from erro

    db = get_db()

    administrador_existente = db.execute(
        """
        SELECT cod_admin
        FROM Administradores
        WHERE email = ? COLLATE NOCASE;
        """,
        (email,)
    ).fetchone()

    if administrador_existente is not None:
        raise click.ClickException(
            "Ja existe um administrador cadastrado com esse e-mail."
        )

    senha_gerada = secrets.token_urlsafe(12)
    senha_hash = generate_password_hash(senha_gerada)

    try:
        db.execute(
            """
            INSERT INTO Administradores (nome_admin, senha, email)
            VALUES (?, ?, ?);
            """,
            (nome, senha_hash, email)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    click.echo("Administrador criado com sucesso.")
    click.echo(f"E-mail: {email}")
    click.echo(f"Senha gerada: {senha_gerada}")
    click.echo("Guarde essa senha agora; ela nao sera exibida novamente.")
