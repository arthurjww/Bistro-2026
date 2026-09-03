import sqlite3
import json
import urllib.parse
import urllib.request
import time

arquivo = # Nome do arquivo do banco de dados

# Lista original de músicas
lista_musicas = [
    # ========== JAZZ ==========
    ("Can't Take My Eyes off You", "Frankie Valli", "Jazz"),
    ("The World We Knew", "Frank Sinatra", "Jazz"),
    ("deep in it", "berlioz, Ted Jasper", "Jazz"),
    ("I Wish You Love", "Nancy Wilson", "Jazz"),
    ("Dream A Little Dream Of Me", "Louis Armstrong", "Jazz"),
    ("Take Five", "The Dave Brubeck Quartet", "Jazz"),
    ("Beyond the Sea", "Bobby Darin", "Jazz"),
    ("That's Life", "Frank Sinatra", "Jazz"),
    ("Ladyfingers", "Herb Alpert & The Tijuana Brass", "Jazz"),
    ("Fly Me To The Moon", "Frank Sinatra, Count Basie", "Jazz"),
    ("My Way", "Frank Sinatra", "Jazz"),
    ("At Last", "Etta James", "Jazz"),
    ("Fever", "Peggy Lee", "Jazz"),
    ("Cheek To Cheek", "Ella Fitzgerald, Louis Armstrong", "Jazz"),
    ("I Put A Spell On You", "Nina Simone", "Jazz"),
    ("Whiplash", "Hank Levy", "Jazz"),
    ("Dream A Little Dream Of Me", "Ella Fitzgerald, Louis Armstrong", "Jazz"),
    ("Feeling Good", "Nina Simone", "Jazz"),
    ("I Say a Little Prayer", "Aretha Franklin", "Jazz"),
    ("Distant Lover", "Marvin Gaye", "Jazz"),
    ("Rhapsody in Blue", "George Gershwin, Columbia Symphony Orchestra, Leonard Bernstein", "Jazz"),
    ("My Song", "Labi Siffre", "Jazz"),
    ("Someday", "Shirley Ann Lee", "Jazz"),
    ("Epilogue", "Justin Hurwitz", "Jazz"),
    ("Bésame Mucho", "Consuelo Velázquez", "Jazz"),
    ("jazz is for ordinary people", "berlioz", "Jazz"),
    ("Strangers In The Night", "Frank Sinatra", "Jazz"),
    ("Georgia on My Mind", "Ray Charles", "Jazz"),
    ("These Foolish Things", "Ella Fitzgerald, Louis Armstrong", "Jazz"),
    ("I'd Rather Go Blind", "Etta James", "Jazz"),
    ("I Fall In Love Too Easily", "Chet Baker", "Jazz"),
    ("My Funny Valentine", "Chet Baker", "Jazz"),
    ("I Believe to My Soul", "Ray Charles", "Jazz"),
    ("What A Wonderful World", "Louis Armstrong", "Jazz"),
    ("Solitude", "Billie Holiday", "Jazz"),
    ("I've Got You Under My Skin", "Frank Sinatra", "Jazz"),
    ("Theme From New York, New York", "Frank Sinatra", "Jazz"),
    ("Blue Moon", "Billie Holiday, Oscar Peterson, Studio ensemble", "Jazz"),
    ("It's Been a Long, Long Time", "Kitty Kallen, Harry James", "Jazz"),
    ("My One And Only Love", "John Coltrane, Johnny Hartman", "Jazz"),
    ("Ain't No Sunshine", "Bill Withers", "Jazz"),
    ("Spooky", "Dusty Springfield", "Jazz"),
    ("A Change Is Gonna Come", "Sam Cooke", "Jazz"),
    ("I've Got a Woman", "Ray Charles", "Jazz"),
    ("In A Sentimental Mood", "Duke Ellington, John Coltrane", "Jazz"),
    ("Smile", "Nat King Cole", "Jazz"),
    ("Let's Stay Together", "Al Green", "Jazz"),
    ("Come Fly With Me", "Frank Sinatra", "Jazz"),
    ("On The Sunny Side Of The Street - Remastered", "Frank Sinatra", "Jazz"),
    ("Ain't That A Kick In The Head", "Dean Martin", "Jazz"),
    ("I Get A Kick Out Of You", "Frank Sinatra", "Jazz"),
    ("Blue Skies", "Ella Fitzgerald", "Jazz"),

    # ========== MPB ==========
    ("Vai Passar", "Chico Buarque", "MPB"),
    ("Se Todos Fossem Iguais a Você", "Nana Caymmi", "MPB"),
    ("Ai Que Saudade D'Ocê", "Elba Ramalho, Zé Ramalho, Geraldo Azevedo", "MPB"),
    ("Gostava Tanto De Você", "Tim Maia", "MPB"),
    ("Azul Da Cor Do Mar", "Tim Maia", "MPB"),
    ("O Que É O Que É?", "Gonzaguinha", "MPB"),
    ("Ovelha Negra", "Rita Lee", "MPB"),
    ("Chega de Saudade", "João Gilberto", "MPB"),
    ("Me Liga", "Os Paralamas Do Sucesso", "MPB"),
    ("Epitáfio", "Titãs", "MPB"),
    ("Amiga Da Minha Mulher", "Seu Jorge", "MPB"),
    ("Burguesinha", "Seu Jorge", "MPB"),
    ("Menina Veneno", "Ritchie", "MPB"),
    ("Exagerado", "Cazuza", "MPB"),
    ("Whisky a Go-Go", "Roupa Nova", "MPB"),
    ("Borbulhas de Amor (Tenho um Coração) [Borbujas de Amor]", "Fagner", "MPB"),
    ("Clareou", "Diogo Nogueira", "MPB"),
    ("Baila Comigo", "Rita Lee, Roberto De Carvalho", "MPB"),
    ("Madalena", "Elis Regina", "MPB"),
    ("Cor De Rosa Choque", "Rita Lee, Roberto De Carvalho", "MPB"),
    ("Escrito Nas Estrelas", "Tetê Espíndola", "MPB"),
    ("Alegria, Alegria - Remastered 2006", "Caetano Veloso", "MPB"),
    ("Estrela", "Gilberto Gil", "MPB"),
    ("O Descobridor Dos Sete Mares", "Tim Maia", "MPB"),
    ("Tropicana", "Alceu Valença", "MPB"),
    ("Garota de Ipanema", "Antônio Carlos Jobim", "MPB"),
    ("Sina", "Djavan", "MPB"),
    ("A Menina Dança", "Novos Baianos", "MPB"),
    ("Canta, Canta Minha Gente", "Sambabook, Martinho Da Vila, Paulinho Da Viola, Diogo Nogueira, Luiz Melodia, Paula Lima", "MPB"),
    ("Eu também quero beijar", "Pepeu Gomes", "MPB"),
    ("Aquarela Do Brasil", "Gal Costa", "MPB"),
    ("Pela Luz Dos Olhos Teus", "Vinícius de Moraes", "MPB"),
    ("Sangue latino", "Ney Matogrosso", "MPB"),
    ("Camarão Que Dorme a Onda Leva", "Sambabook, Zeca Pagodinho, Dudu Nobre, Mumuzinho, Djavan, Sombrinha, Arlindo Cruz", "MPB"),
    ("Tarde em Itapuã", "Toquinho, Vinícius de Moraes, Ophélie Gaillard, Romain Lécuyer", "MPB"),
    ("Como uma onda", "Lulu Santos", "MPB"),
    ("Não Quero Dinheiro", "Tim Maia", "MPB"),
    ("Eu Só Quero um Xodó", "Gilberto Gil", "MPB"),
    ("Ai Que Saudade D'Ocê", "Fábio Jr., Elba Ramalho", "MPB"),
    ("Como Nossos Pais", "Elis Regina", "MPB"),
    ("Flor de Lis", "Djavan", "MPB"),
    ("Brasil", "Gal Costa", "MPB"),

    # ========== ROCK ==========
    ("Thunderstruck", "AC/DC", "Rock"),
    ("Enter Sandman", "Metallica", "Rock"),
    ("Tears in Heaven", "Eric Clapton", "Rock"),
    ("Patience", "Guns N' Roses", "Rock"),
    ("Every Breath You Take", "The Police", "Rock"),
    ("What's Up?", "4 Non Blondes", "Rock"),
    ("November Rain", "Guns N' Roses", "Rock"),
    ("Smells Like Teen Spirit", "Nirvana", "Rock"),
    ("Welcome To The Jungle", "Guns N' Roses", "Rock"),
    ("Paranoid", "Black Sabbath", "Rock"),
    ("Rock And Roll All Nite", "KISS", "Rock"),
    ("In the End", "Linkin Park", "Rock"),
    ("Come As You Are", "Nirvana", "Rock"),
    ("Paradise City", "Guns N' Roses", "Rock"),
    ("Everybody Wants To Rule The World", "Tears For Fears", "Rock"),
    ("I Was Made For Lovin' You", "KISS", "Rock"),
    ("I Love Rock 'N Roll", "Joan Jett & the Blackhearts", "Rock"),
    ("It's My Life", "Bon Jovi", "Rock"),
    ("Don't Stop Me Now", "Queen", "Rock"),
    ("Let It Be", "The Beatles", "Rock"),
    ("The Show Must Go On", "Queen", "Rock"),
    ("In My Life", "The Beatles", "Rock"),
    ("Hotel California", "Eagles", "Rock"),
    ("Knockin' On Heaven's Door", "Guns N' Roses", "Rock"),
    ("Livin' On A Prayer", "Bon Jovi", "Rock"),
    ("Here Comes The Sun", "The Beatles", "Rock"),
    ("Bohemian Rhapsody", "Queen", "Rock"),
    ("Losing My Religion", "R.E.M.", "Rock"),
    ("Don't Cry", "Guns N' Roses", "Rock"),
    ("Have You Ever Seen The Rain", "Creedence Clearwater Revival", "Rock"),
    ("Shadows Of Our Evening Tides", "Alex Henry Foster, Allen Ginsberg", "Rock"),
    ("Last Kiss", "Pearl Jam", "Rock"),
    ("Sweet Child O' Mine", "Guns N' Roses", "Rock"),

    # ========== POP ==========
    ("Rock Your Body", "Justin Timberlake", "Pop"),
    ("SexyBack", "Justin Timberlake, Timbaland", "Pop"),
    ("My Boo", "USHER, Alicia Keys", "Pop"),
    ("So Sick", "Ne-Yo", "Pop"),
    ("Umbrella", "Rihanna, JAY-Z", "Pop"),
    ("Poker Face", "Lady Gaga", "Pop"),
    ("Call My Name", "Prince", "Pop"),
    ("Viva La Vida", "Coldplay", "Pop"),
    ("Butterflies", "Michael Jackson", "Pop"),
    ("You Rock My World", "Michael Jackson", "Pop"),
    ("Beautiful Day", "U2", "Pop"),
    ("Bad Day", "Daniel Powter", "Pop"),
    ("Fix You", "Coldplay", "Pop"),
    ("Clocks", "Coldplay", "Pop"),
    ("Heaven Can Wait", "Michael Jackson", "Pop"),
    ("One More Chance", "Michael Jackson", "Pop"),
    ("She Will Be Loved", "Maroon 5", "Pop"),
    ("This Love", "Maroon 5", "Pop"),
    ("You're Beautiful", "James Blunt", "Pop"),
    ("Break of Dawn", "Michael Jackson", "Pop"),
    ("Toxic", "Britney Spears", "Pop"),
    ("Shape of My Heart", "Backstreet Boys", "Pop"),
    ("The Call", "Backstreet Boys", "Pop"),
]

def buscar_info_itunes(nome, artista):
    """Busca o link do preview de áudio e a URL da capa no iTunes."""
    termo = f"{nome} {artista}"
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(termo)}&media=music&limit=1"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode())
            if dados.get("resultCount", 0) > 0:
                resultado = dados["results"][0]
                preview_url = resultado.get("previewUrl", "")
                # Substitui a imagem 100x100 por uma de alta resolução 600x600
                capa_url = resultado.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                return preview_url, capa_url
    except Exception as e:
        print(f"Erro ao buscar '{nome}': {e}")
    
    return "", ""

def criar_tabela(arquivo):
    with sqlite3.connect(arquivo) as conexao:
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS musicas(
                num INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                artista TEXT NOT NULL,
                link TEXT,
                capa TEXT,
                estilo TEXT NOT NULL
            )
        """)

def cadastrar_musicas(lista, arquivo):
    lista_processada = []
    
    print("Buscando links de preview e capas no iTunes...")
    for idx, item in enumerate(lista, 1):
        nome, artista, estilo = item
        link_preview, link_capa = buscar_info_itunes(nome, artista)
        
        lista_processada.append((nome, artista, link_preview, link_capa, estilo))
        print(f"[{idx}/{len(lista)}] Processado: {nome} - {artista}")
        
        # Pausa para respeitar os limites de requisição da API
        time.sleep(0.1)

    try:
        with sqlite3.connect(arquivo) as conexao:
            cursor = conexao.cursor()
            cursor.executemany("""
                INSERT INTO musicas (nome, artista, link, capa, estilo)
                VALUES (?, ?, ?, ?, ?)
            """, lista_processada)
            
            print(f"\n{len(lista_processada)} músicas cadastradas com sucesso!")
            
    except sqlite3.IntegrityError as e:
        print("Erro de integridade:", e)
    except sqlite3.Error as e:
        print("Erro no banco de dados:", e)

criar_tabela(arquivo)
cadastrar_musicas(lista_musicas, arquivo)
