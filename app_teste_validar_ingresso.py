#from backend import app

#if __name__ == "__main__":
    #app.run(port=8080)

#TODO: as linhas acima foram comentadas para testar o site que abre para validação do ingresso localmente. - 24/08s
import os
from flask import Flask
from backend.ingressos.gerador_pdf import gerador_pdf

app = Flask(__name__)

# Configura o caminho absoluto do banco de dados para a aplicação
app.config['DATABASE'] = os.path.join(app.root_path, 'database', 'teste.db')

# Registra as rotas do Blueprint
app.register_blueprint(gerador_pdf)

if __name__ == '__main__':
    # host='0.0.0.0' permite que outros aparelhos no mesmo Wi-Fi acessem o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)