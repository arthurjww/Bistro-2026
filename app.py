from backend import app
from backend.banco_de_dados import create_all
from backend.mapa_mesas.lugares import seed_lugares

with app.app_context():
    create_all()
    seed_lugares()

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=8080, debug=True)