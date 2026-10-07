import sqlite3

conexao = sqlite3.connect("database/teste.db")

conexao.execute("""
    UPDATE Pedido
    SET status = 'approved'
    WHERE order_id = 1353231821
""")

conexao.commit()

print("Pedido marcado como approved!")

conexao.close()