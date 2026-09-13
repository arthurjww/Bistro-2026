import sqlite3
db = sqlite3.connect("database/teste.db")  # ajuste o caminho se necessário
print("Total de lugares:", db.execute("SELECT COUNT(*) FROM Lugares").fetchone())
print("Lugar A1:", db.execute("SELECT * FROM Lugares WHERE cod_lugar = 'A1'").fetchone())