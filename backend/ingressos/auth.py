from .. import login_manager
from ..banco_de_dados import get_db
from flask import Blueprint, flash, redirect, url_for, render_template
from flask_login import UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from werkzeug.security import check_password_hash


# class para utilizar flask_login
class Admin(UserMixin):
    def __init__(self, cod_admin, nome_admin, senha, email):
        self.id = cod_admin
        self.nome = nome_admin
        self.senha = senha
        self.email = email


# classe para formulário do html
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField()


# classe que verifica se o usuário está logado
@login_manager.user_loader
def user_loader(admin_id):
    admin = get_db().execute(
        '''
        SELECT *
        FROM Administradores
        WHERE cod_admin = ?
        ''',
        (admin_id,)
    ).fetchone()

    if admin:
        return Admin(
            admin['cod_admin'],
            admin['nome_admin'],
            admin['senha'],
            admin['email']
        )

    return None


#TODO: COLOCAR subdomain='admin' caso queira admin.site.com.br
auth = Blueprint('auth', __name__)


# rota para página de login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email_input = form.email.data
        senha_input = form.senha.data

        admin = get_db().execute(
            '''
            SELECT *
            FROM Administradores
            WHERE email = ?
            ''',
            (email_input,)
        ).fetchone()

        if not admin or not check_password_hash(admin['senha'], senha_input):
            flash('Verifique suas informações de login', 'error')
            return redirect(url_for('auth.login'))

        admin_login = Admin(
            admin['cod_admin'],
            admin['nome_admin'],
            admin['senha'],
            admin['email']
        )
        login_user(admin_login)
        return redirect(url_for('routes.index'))

    return render_template('ingressos/login.html', form=form)


#rota para logout
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))