from flask import Flask
from flask_login import LoginManager
from pathlib import Path


main_folder = Path(__file__).resolve().parent.parent
DATABASE = main_folder / 'database' / 'database.db'


app = Flask(
    __name__,
    static_folder= main_folder / 'frontend' / 'static',
    template_folder= main_folder / 'frontend' / 'templates',
)


login_manager = LoginManager(app)


#TODO: Mudar chave secreta no lançamento
app.config['SECRET_KEY'] = 'CETEC'

app.config['DATABASE'] = DATABASE

login_manager.login_view = 'login'
login_manager.login_message = 'Somente admins tem autorização para acessar essa página'


from .ingressos.routes import routes
from .ingressos.auth import auth

app.register_blueprint(routes)
app.register_blueprint(auth)


# testes para pastas
print("main_folder:", main_folder)
print("template_folder:", app.template_folder)
print("template existe:", (main_folder / 'frontend' / 'templates').exists())
print("index existe:", (main_folder / 'frontend' / 'templates' / 'ingressos' / 'index.html').exists())