import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

main_folder = Path(__file__).resolve().parent.parent.parent
bundle_folder = main_folder.parent

load_dotenv(bundle_folder / ".env")


def _resolver_database():
    configurado = os.getenv("BISTRO_DATABASE_PATH", "").strip()
    if configurado:
        caminho = Path(configurado).expanduser()
        if not caminho.is_absolute():
            caminho = (bundle_folder / caminho).resolve()
    else:
        caminho = bundle_folder / "database" / "bistro.db"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho


DATABASE = _resolver_database()

app = Flask(
    __name__,
    template_folder=main_folder / "frontend" / "templates",
    static_folder=main_folder / "frontend" / "static",
)
app.config["DATABASE"] = str(DATABASE)

chave_secreta = os.getenv("RELATORIOS_SECRET_KEY", "").strip()
if not chave_secreta:
    raise RuntimeError(
        "A variável RELATORIOS_SECRET_KEY não foi configurada. "
        "Defina-a no .env compartilhado."
    )

app.config["SECRET_KEY"] = chave_secreta
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

login_manager = LoginManager()
login_manager.login_view = "auth_relatorios.login"
login_manager.login_message = "Faça login para acessar os relatórios."
login_manager.login_message_category = "erro"
login_manager.session_protection = "strong"
login_manager.init_app(app)

from ..banco_de_dados import close_connection, create_all
app.teardown_appcontext(close_connection)

from .auth import auth_relatorios
from .comandos import criar_admin
from .routes import relatorios

app.register_blueprint(auth_relatorios)
app.register_blueprint(relatorios)
app.cli.add_command(criar_admin)

# Só cria/migra estrutura. Nunca apaga ingressos, reservas ou votos.
with app.app_context():
    create_all()
