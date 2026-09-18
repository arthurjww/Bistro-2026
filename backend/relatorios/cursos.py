from pathlib import Path
import unicodedata

ARQUIVO_LISTA = Path(__file__).with_name("lista_alunos_cursos.txt")

def normalizar_nome(nome):
    nome_normalizado = unicodedata.normalize("NFD",nome.casefold())

    nome_sem_acentos = "".join(
        caractere
        for caractere in nome_normalizado
        if unicodedata.category(caractere) != "Mn"
    )

    return " ".join(nome_sem_acentos.split())


def carregar_cursos_por_nome():
    cursos_por_nome = {}

    if not ARQUIVO_LISTA.exists():
        return cursos_por_nome

    linhas = ARQUIVO_LISTA.read_text(encoding="utf-8").splitlines()

    for linha in linhas:
        linha = linha.strip().lstrip("\ufeff")

        if not linha:
            continue

        if linha.startswith("Nome completo"):
            continue

        partes = linha.split("|", maxsplit=1)

        if len(partes) != 2:
            continue

        nome, curso = partes
        nome = nome.strip()
        curso = curso.strip()

        cursos_por_nome[normalizar_nome(nome)] = curso

    return cursos_por_nome


CURSOS_POR_NOME = carregar_cursos_por_nome()


def obter_curso_por_nome(nome):
    if not nome:
        return None

    return CURSOS_POR_NOME.get(normalizar_nome(nome))