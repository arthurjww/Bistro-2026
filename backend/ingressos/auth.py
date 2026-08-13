from .. import app, login_manager, banco_de_dados
from ..banco_de_dados import get_db
from flask import Blueprint
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


class Admin(UserMixin):
    def __init__(self, cod_admin, nome_admin, senha, email):
        self.id = cod_admin
        self.nome = nome_admin
        self.senha = senha
        self.email = email


class LoginForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField()


@login_manager.user_loader()
def user_loader(admin_id):
    admin = get_db().execute(
        '''
        SELECT cod_admin, nome_admin, senha, email
        FROM Administradores
        WHERE cod_admin = ?
        ''',
        (admin_id,)
    ).fetchone()

    if admin:
        return Admin(admin[0], admin[1], admin[2], admin[3])

    return None


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        nome_input = form.nome.data
        email_input = form.email.data
        senha_input = form.senha.data

        admin = get_db().execute(
            '''
            SELECT cod_admin, nome_admin, senha, email
            FROM Administradores
            WHERE email = ?
            ''',
            (email_input,)
        ).fetchone()