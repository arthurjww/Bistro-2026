from flask import g, Flask
from flask_login import LoginManager
from
from pathlib import Path
import sqlite3

main_folder = Path(__name__).resolve().parent.parent

app = Flask(
    __name__,
    static_folder= main_folder / 'frontend' / 'static',
    template_folder= main_folder / 'frontend' / 'templates',
)

#TODO: Mudar chave secreta no lançamento
app.config['SECRET_KEY'] = 'CETEC'


DATABASE = main_folder / 'database' / 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()