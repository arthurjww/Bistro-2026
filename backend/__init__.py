from pathlib import Path

from flask import Flask
from flask_login import LoginManager

main_folder = Path(__file__).resolve().parent.parent

#se o database não existir cria automaticamente
DATABASE_FOLDER = main_folder / "database"
DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE = DATABASE_FOLDER / "teste.db"  #TODO: teste.db. alterar depois!



app = Flask (
    __name__,
    static_folder= (
        main_folder / "frontend" / "static"
    ),
    template_folder = (
        main_folder / "frontend" / "templates"
        )
    )

#TODO: Mudar chave secreta no lançamento
app.config["SECRET_KEY"] = "CETEC"
app.config["DATABASE"] = str (DATABASE)


from .banco_de_dados import create_all, close_connection

app.teardown_appcontext(close_connection)

#FLASK LOGIN
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = (
    "Somente admins têm autorização para acessar essa página"
)

#BluePrints

from .ingressos.routes import routes
from .ingressos.auth import auth
from .ingressos.gerador_pdf import gerador_pdf
app.register_blueprint(gerador_pdf)

app.register_blueprint(routes)
app.register_blueprint(auth)

with app.app_context():
    create_all()

    # testes para pastas
    print("main_folder:", main_folder)
    print("template_folder:", app.template_folder)

    print(
        "template existe:",
        (main_folder / "frontend" / "templates").exists()
    )

    print(
        "index existe:",
        (
            main_folder
            / "frontend"
            / "templates"
            / "ingressos"
            / "index.html"
        ).exists()
    )

