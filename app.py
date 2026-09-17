from backend import app
from backend.banco_de_dados import create_all
from backend.mapa_mesas.lugares import Salao1, Salao2

with app.app_context():
    create_all()
    Salao1().seed_lugares()
    Salao2().seed_lugares()
    
if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=8080, debug=True)