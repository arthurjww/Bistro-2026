from flask import Blueprint, render_template
from .vendas import obter_total_ingressos
from .vendas import obter_ingressos_pagos
from .vendas import obter_ingressos_nao_pagos
from .vendas import obter_ingressos_restantes
from .vendas import obter_ingressos_restantes_por_aluno
from .vendas import obter_lista_vendas

# se quiser usar subdomain adicionar: subdomain='admin'
relatorios=Blueprint('relatorios', __name__)

@relatorios.get('/relatorios')
def painel_relatorios():
    total_ingressos = obter_total_ingressos()
    ingressos_pagos = obter_ingressos_pagos()
    ingressos_nao_pagos = obter_ingressos_nao_pagos()
    ingressos_restantes = obter_ingressos_restantes()
    lista_ingressos_restantes = obter_ingressos_restantes_por_aluno()
    lista_vendas = obter_lista_vendas()

    return render_template(
        'relatorios/index.html',
        total_ingressos = total_ingressos,
        ingressos_pagos = ingressos_pagos,
        ingressos_naopagos = ingressos_nao_pagos,
        ingressos_restantes = ingressos_restantes,
        lista_ingressos_restantes = lista_ingressos_restantes,
        lista_vendas = lista_vendas
    )

