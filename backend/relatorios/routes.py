from flask import Blueprint, render_template, request
from flask_login import login_required
from .vendas import obter_total_ingressos
from .vendas import obter_ingressos_pagos
from .vendas import obter_ingressos_nao_pagos
from .vendas import obter_ingressos_restantes
from .vendas import obter_ingressos_restantes_por_aluno
from .vendas import obter_lista_vendas
from .restricoes import obter_lista_restricoes
from .financeiro import obter_lista_financeiro
from .visao_geral import obter_alunos_filtro
from .visao_geral import obter_participantes_filtro
from .visao_geral import obter_detalhes_participante
from .resumo_participantes import obter_resumo_participantes
from .musicas import obter_top_5_musicas

# se quiser usar subdomain adicionar: subdomain='admin'
relatorios = Blueprint('relatorios', __name__)

@relatorios.get('/relatorios')
@login_required
def painel_relatorios():
    numero_ingresso = request.args.get('participante', type=int)
    codigo_aluno = request.args.get('aluno')
    total_ingressos = obter_total_ingressos()
    ingressos_pagos = obter_ingressos_pagos()
    ingressos_nao_pagos = obter_ingressos_nao_pagos()
    ingressos_restantes = obter_ingressos_restantes()
    lista_ingressos_restantes = obter_ingressos_restantes_por_aluno()
    lista_vendas = obter_lista_vendas()
    lista_restricoes = obter_lista_restricoes()
    lista_financeiro = obter_lista_financeiro()
    lista_alunos = obter_alunos_filtro()
    lista_compradores = obter_participantes_filtro(codigo_aluno)
    lista_resumo = obter_resumo_participantes()
    lista_musicas = obter_top_5_musicas()

    detalhes_participante = None

    if numero_ingresso is not None:
        detalhes_participante = obter_detalhes_participante(numero_ingresso)

    return render_template(
        'relatorios/index.html',
        total_ingressos = total_ingressos,
        ingressos_pagos = ingressos_pagos,
        ingressos_naopagos = ingressos_nao_pagos,
        ingressos_restantes = ingressos_restantes,
        lista_ingressos_restantes = lista_ingressos_restantes,
        lista_vendas = lista_vendas,
        lista_restricoes = lista_restricoes,
        lista_financeiro = lista_financeiro,
        lista_alunos = lista_alunos,
        lista_compradores = lista_compradores,
        detalhes_participante = detalhes_participante,
        lista_resumo = lista_resumo,
        lista_musicas = lista_musicas,
    )

