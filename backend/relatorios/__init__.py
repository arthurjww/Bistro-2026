import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from pathlib import Path

load_dotenv()

main_folder = Path(__file__).resolve().parent.parent.parent

DATABASE = main_folder / "database" / "teste.db"

app = Flask(__name__, template_folder=main_folder / "frontend" / "templates")

app.config["DATABASE"] = str(DATABASE)

chave_secreta = os.getenv("RELATORIOS_SECRET_KEY")

if not chave_secreta:
    raise RuntimeError("A variável RELATORIOS_SECRET_KEY não foi configurada.")

app.config["SECRET_KEY"] = chave_secreta
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

login_manager = LoginManager()

login_manager.login_view = "auth_relatorios.login"
login_manager.login_message = ("Faça login para acessar os relatórios.")
login_manager.login_message_category = "erro"
login_manager.session_protection = "strong"

login_manager.init_app(app)

from ..banco_de_dados import close_connection

app.teardown_appcontext(close_connection)

from .auth import auth_relatorios
from .comandos import criar_admin
from .routes import relatorios

app.register_blueprint(auth_relatorios)
app.register_blueprint(relatorios)
app.cli.add_command(criar_admin)


