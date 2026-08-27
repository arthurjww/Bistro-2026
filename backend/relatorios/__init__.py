from flask import Flask

app = Flask(__name__)

from .routes import relatorios

app.register_blueprint(relatorios)