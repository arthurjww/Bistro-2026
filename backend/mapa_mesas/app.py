from pathlib import Path
from flask import Flask
from routes import bp_lugares
from banco_de_dados import create_all, close_connection
from lugares import seed_lugares

app = Flask(__name__)
app.config["SECRET_KEY"] = "CETEC"

project_root = Path(__file__).resolve().parents[2]
database_folder = project_root / 'database'
database_folder.mkdir(parents=True, exist_ok=True)
app.config['DATABASE'] = str(database_folder / 'teste.db')

app.teardown_appcontext(close_connection)
app.register_blueprint(bp_lugares)

with app.app_context():
    create_all()
    seed_lugares()

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=5000, debug=True)