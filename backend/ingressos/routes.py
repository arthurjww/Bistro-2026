from ..banco_de_dados import get_db
from flask import Blueprint, flash, redirect, url_for, render_template
from flask_login import login_required, current_user


routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    return render_template('ingressos/index.html', logado=current_user.is_authenticated)