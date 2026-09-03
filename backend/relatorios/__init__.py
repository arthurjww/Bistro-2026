from pathlib import Path

from flask import Flask


main_folder = Path(__file__).resolve().parent.parent.parent

DATABASE = main_folder / "database" / "teste.db"

app = Flask(__name__, template_folder=main_folder / "frontend" / "templates")

app.config["DATABASE"] = str(DATABASE)

from ..banco_de_dados import close_connection

app.teardown_appcontext(close_connection)

from .routes import relatorios

app.register_blueprint(relatorios)



