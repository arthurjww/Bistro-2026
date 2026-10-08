import os
from pathlib import Path
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

main_folder = Path(__file__).resolve().parent.parent
bundle_folder = main_folder.parent
load_dotenv(bundle_folder / ".env", override=False)
configured = os.getenv("BISTRO_DATABASE_PATH", "database/bistro.db")
DATABASE = Path(configured).expanduser()
if not DATABASE.is_absolute():
    DATABASE = (bundle_folder / DATABASE).resolve()
DATABASE.parent.mkdir(parents=True, exist_ok=True)
app = Flask(__name__, static_folder=main_folder / "frontend" / "static", template_folder=main_folder / "frontend" / "templates")
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config["SECRET_KEY"] = os.environ["INGRESSOS_SECRET_KEY"]
app.config["DATABASE"] = str(DATABASE)

# Configurações de Email puxadas do .env
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "0") or 0) or None
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

# Ajuste automático de SSL/TLS baseado na porta 465 ou 587
app.config["MAIL_USE_SSL"] = app.config["MAIL_PORT"] == 465
app.config["MAIL_USE_TLS"] = app.config["MAIL_PORT"] == 587


from .banco_de_dados import close_connection

app.teardown_appcontext(close_connection)

#BluePrints

from .ingressos.routes import routes
from .ingressos.gerador_pdf import gerador_pdf
from .mapa_mesas.routes import bp_lugares
app.register_blueprint(gerador_pdf)
app.register_blueprint(bp_lugares)
app.register_blueprint(routes)