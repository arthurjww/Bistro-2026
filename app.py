from backend import app
from backend.banco_de_dados import create_all
from backend.mapa_mesas.lugares import MapaLugares

with app.app_context():
    create_all()
    MapaLugares().seed_lugares()
    

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=5002, debug=True)