from ..banco_de_dados import get_db
from . import login_manager
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user, UserMixin
from werkzeug.security import check_password_hash

auth_relatorios = Blueprint('auth_relatorios', __name__)

class Administrador(UserMixin):
    def __init__(self, cod_admin, nome_admin, email):
        self.id = cod_admin
        self.nome = nome_admin
        self.email = email

class LoginAdministradorForm(FlaskForm):
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(),
            Email(),
            Length(max=255)
        ]
    )

    senha = PasswordField(
        'Senha',
        validators=[
            DataRequired(),
            Length(min=4, max=128)
        ]
    )

    submit = SubmitField('Entrar')

@login_manager.user_loader
def carregar_administrador(admin_id):
    try:
        cod_admin = int(admin_id)
    except (TypeError, ValueError):
        return None

    admin = get_db().execute(
        '''
        SELECT
            cod_admin,
            nome_admin,
            email
        FROM Administradores
        WHERE cod_admin = ?;
        ''',
        (cod_admin,)
    ).fetchone()

    if admin is None:
        return None

    return Administrador(
        admin['cod_admin'],
        admin['nome_admin'],
        admin['email']
    )

@auth_relatorios.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('relatorios.painel_relatorios'))

    form = LoginAdministradorForm()

    if form.validate_on_submit():
        email_informado = form.email.data.strip().lower()
        senha_informada = form.senha.data

        admin = get_db().execute(
            '''
            SELECT
                cod_admin,
                nome_admin,
                senha,
                email
            FROM Administradores
            WHERE LOWER(email) = ?;
            ''',
            (email_informado,)
        ).fetchone()

        if admin is None or not check_password_hash(admin['senha'], senha_informada):
            flash(
                'E-mail ou senha incorretos.',
                'erro'
            )
            return redirect(url_for('auth_relatorios.login'))

        administrador = Administrador(
            admin['cod_admin'],
            admin['nome_admin'],
            admin['email']
        )

        login_user(administrador)

        return redirect(url_for('relatorios.painel_relatorios'))

    return render_template('relatorios/login.html', form=form)

@auth_relatorios.get('/logout')
@login_required
def logout():
    logout_user()

    flash(
        'Sessão encerrada com sucesso.',
        'sucesso'
    )

    return redirect(url_for('auth_relatorios.login'))