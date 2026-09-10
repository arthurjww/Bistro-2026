import sqlite3
import sys
import os
from flask import Flask, render_template, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Trata a importação tanto se estiver na raiz quanto na pasta 'backend'

from banco_de_dados import get_db, close_connection, create_all
import musicas as msc
cadastrar_musicas = msc.cadastrar_musicas

app = Flask(__name__, template_folder="C:\\Users\\hdpai\\Downloads\\bistro\\Bistro-2026\\frontend\\templates\\musicas")

# Configura o caminho do banco de dados SQLite
app.config["DATABASE"] = "database.db"

# Registra a função para fechar o banco ao fim de cada requisição
app.teardown_appcontext(close_connection)


def inicializar_banco():
    """Cria as tabelas, garante a coluna de votos e popula o banco se estiver vazio."""
    with app.app_context():
        create_all()
        db = get_db()
        cursor = db.cursor()

        # Garante que a coluna 'votos' existe na tabela de músicas
        try:
            cursor.execute("ALTER TABLE musicas ADD COLUMN votos INTEGER DEFAULT 0")
            db.commit()
        except sqlite3.OperationalError:
            pass  # A coluna já existe

        # Remove músicas repetidas pelo mesmo título e estilo
        cursor.execute("""
            DELETE FROM musicas
            WHERE num NOT IN (
                SELECT MIN(num)
                FROM musicas
                GROUP BY LOWER(TRIM(nome)), LOWER(TRIM(estilo))
            )
        """)
        db.commit()

        # Se não houver músicas, cadastra a lista inicial
        cursor.execute("SELECT COUNT(*) FROM musicas")
        if cursor.fetchone()[0] == 0:
            print("Iniciando cadastro das músicas no banco de dados...")
            cadastrar_musicas()


# Executa a inicialização do banco ao carregar a aplicação
inicializar_banco()


@app.route("/", methods=["GET", "POST"])
def votacao():
    mensagem = ""
    mostrar_resultados = False
    db = get_db()
    cursor = db.cursor()

    # Busca os estilos únicos de músicas cadastrados no banco
    cursor.execute("SELECT DISTINCT estilo FROM musicas ORDER BY estilo ASC")
    estilos = [row["estilo"] for row in cursor.fetchall()]

    if request.method == "POST":
        votos_recebidos = {}
        faltou_algum = False

        # Verifica o voto enviado para cada um dos estilos (enquetes)
        for estilo in estilos:
            musica_id = request.form.get(estilo)
            if musica_id:
                votos_recebidos[estilo] = musica_id
            else:
                faltou_algum = True

        if faltou_algum:
            mensagem = "Por favor, escolha uma opção em TODAS as enquetes antes de enviar!"
        else:
            # Incrementa os votos das músicas selecionadas
            for musica_id in votos_recebidos.values():
                cursor.execute(
                    "UPDATE musicas SET votos = votos + 1 WHERE num = ?",
                    (musica_id,)
                )
            db.commit()
            mensagem = "Seus votos foram registrados com sucesso!"
            mostrar_resultados = True

    # Busca as 5 músicas com mais votos de cada estilo para exibir no formulário
    enquetes = {}
    for estilo in estilos:
        cursor.execute("""
            SELECT num, nome, artista, link, capa, estilo, votos 
            FROM musicas 
            WHERE estilo = ? 
            ORDER BY votos DESC, nome ASC
            LIMIT 5
        """, (estilo,))
        enquetes[estilo] = cursor.fetchall()

    return render_template(
        "index.html",
        enquetes=enquetes,
        mensagem=mensagem,
        mostrar_resultados=mostrar_resultados
    )


if __name__ == "__main__":
    app.run(debug=True, port=4444)