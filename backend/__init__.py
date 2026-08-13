from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from pathlib import Path


main_folder = Path(__name__).resolve().parent.parent
DATABASE = main_folder / 'database' / 'database.db'


app = Flask(
    __name__,
    static_folder= main_folder / 'frontend' / 'static',
    template_folder= main_folder / 'frontend' / 'templates',
)


login_manager = LoginManager(app)
bcrypt = Bcrypt(app)


#TODO: Mudar chave secreta no lançamento
app.config['SECRET_KEY'] = 'CETEC'

app.config['DATABASE'] = DATABASE

login_manager.login_view = 'login'
login_manager.login_message = 'Somente admins tem autorização para acessar essa página'


from .ingressos.auth import auth

app.register_blueprint(auth)