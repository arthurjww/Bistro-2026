import sqlite3

# Conecta ao banco de dados no caminho indicado no projeto
conn = sqlite3.connect('database/teste.db')
cursor = conn.cursor()

# Habilita a checagem de Chaves Estrangeiras no SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# 1. Garante que o Aluno exista (necessário para a FOREIGN KEY do Lugar e do Ingresso)
# cod_aluno precisa ter exatamente 6 caracteres
cursor.execute("""
    INSERT OR IGNORE INTO Aluno (cod_aluno, nome_aluno, usos_restantes)
    VALUES (?, ?, ?)
""", ('ALU123', 'João Silva', 2))

# 2. Garante que o Lugar exista (necessário para a FOREIGN KEY do Ingresso)
# cod_lugar <= 3 caracteres | mesa <= 1 caractere
cursor.execute("""
    INSERT OR IGNORE INTO Lugares (cod_lugar, cod_aluno, mesa, ocupado)
    VALUES (?, ?, ?, ?)
""", ('M04', 'ALU123', '4', 1))

# 3. Insere o Ingresso respeitando as regras NOT NULL e CHECK da sua tabela
cursor.execute("""
    INSERT INTO Ingresso (
        nome, 
        email_envio, 
        data_compra, 
        token_QR, 
        cod_lugar, 
        cod_aluno, 
        valor_pago, 
        tipo_ingresso, 
        foi_pago
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'João Silva', 
    'joao@exemplo.com', 
    '24/08/2026', 
    'TOK123', 
    'M04',         # cod_lugar max 3 caracteres (Mesa 04 estourava o limite)
    'ALU123',      # cod_aluno obrigatório (NOT NULL) e exatamente 6 caracteres
    0.00,          # valor_pago obrigatório (NOT NULL)
    0, 
    1
))

conn.commit()
conn.close()

print("✅ Ingresso de teste inserido com sucesso!")
print("🔑 Token de teste: TOK123")