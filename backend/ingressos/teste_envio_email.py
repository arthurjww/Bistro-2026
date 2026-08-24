from backend.ingressos.email_envio import enviar_email

print("Iniciando teste de email...") #teste 

enviar_email(
    destinatario="",
    assunto="Teste - Bistrô 2026",
    mensagem="""
Olá!

Este é um teste do sistema de envio de emails
do projeto Bistrô 2026.

Se você recebeu este email, o SMTP está funcionando.

Atenciosamente,
Bistrô 2026
"""
)

print("Email enviado com sucesso!") #teste

