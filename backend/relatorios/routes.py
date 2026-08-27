from flask import Blueprint

# se quiser usar subdomain adicionar: subdomain='admin'
relatorios=Blueprint('relatorios', __name__)

@relatorios.get('/relatorios')
def painel_relatorios():
    return 'pagina relatorios'