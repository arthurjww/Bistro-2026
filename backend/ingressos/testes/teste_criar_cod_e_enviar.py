from backend.ingressos.criar_aluno import criar_alunos, enviar_cod
from backend import app

with app.app_context():
    criar_alunos()
    enviar_cod()