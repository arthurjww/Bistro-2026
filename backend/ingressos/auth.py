from .. import app, login_manager, banco_de_dados
from ..banco_de_dados import get_db
from flask import Blueprint
from flask_login import UserMixin


class Admin(UserMixin):
    def __init__(self, cod_admin, nome_admin, senha, email):
        self.id = cod_admin
        self.nome = nome_admin
        self.senha = senha
        self.email = email


@login_manager.user_loader()
def user_loader(admin_id):
    cursor = get_db().cursor()

    admin = cursor.execute(
        'SELECT cod_admin, nome_admin, senha, email FROM Administradores WHERE cod_admin = ?',
        (admin_id,)
    ).fetchone()

    if admin:
        return Admin(admin[0], admin[1], admin[2], admin[3])

    return None


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    pass
