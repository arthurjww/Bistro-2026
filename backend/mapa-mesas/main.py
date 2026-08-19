# retornar 4 valores para banco de dados: cod_lugar, cod_aluno, mesa, ocupado
import json
import os


class Assento:
    LIVRE = 0
    OCUPADO = 1
    NO_PAGAMENTO = 2

    _NOMES_STATUS = {
        LIVRE: "Livre",
        OCUPADO: "Ocupado",
        NO_PAGAMENTO: "Em pagamento",
    }

    def __init__(self, numero, status=LIVRE):
        self.set_numero(numero)
        self.set_status(status)

    #getter
    def get_numero(self):
        return self._numero

    def get_status(self):
        return self._status

    # setters (com validação) 
    def set_numero(self, valor):
        if not isinstance(valor, int) or valor < 1:
            raise ValueError("O número do assento deve ser um inteiro positivo.")
        self._numero = valor

    def set_status(self, valor):
        if valor not in self._NOMES_STATUS:
            raise ValueError("Status de assento inválido.")
        self._status = valor

    def esta_disponivel(self):
        return self._status == self.LIVRE

    def nome_status(self):
        return self._NOMES_STATUS[self._status]

    def __str__(self):
        return f"{self._numero}:{self.nome_status()}"


class Mesa:
    def __init__(self, letra, situacao):
        self.set_letra(letra)
        self._assentos = [
            Assento(numero=i + 1, status=status)
            for i, status in enumerate(situacao)
        ]

    # getters 
    def get_letra(self):
        return self._letra

    def total_assentos(self):
        return len(self._assentos)

    # setter 
    def set_letra(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("A letra da mesa não pode ser vazia.")
        self._letra = str(valor).strip().upper()

    # acesso a um assento específico 
    def get_assento(self, numero):
        indice = numero - 1
        if indice < 0 or indice >= len(self._assentos):
            raise ValueError(f"A mesa {self._letra} não possui o assento {numero}.")
        return self._assentos[indice]

    def para_lista_status(self):
        return [assento.get_status() for assento in self._assentos]

    def __str__(self):
        assentos = ", ".join(str(a) for a in self._assentos)
        return f"Mesa {self._letra} ({self.total_assentos()} lugares) -> {assentos}"


class Salao:
    CAMINHO_PADRAO = "lugares.json"

    LAYOUT_MESAS = {
        "A": 8, "B": 6, "C": 8, "D": 8, "E": 8, "F": 8, "G": 8,
        "H": 6, "I": 6, "J": 6, "K": 6, "L": 6, "M": 6, "N": 6,
        "O": 6, "P": 8,
    }

    def __init__(self, caminho=CAMINHO_PADRAO):
        self.set_caminho(caminho)

    # getter/setter
    def get_caminho(self):
        return self._caminho

    def set_caminho(self, valor):
        if not valor or not valor.strip():
            raise ValueError("O caminho do arquivo não pode ser vazio.")
        self._caminho = valor.strip()

    def _layout_zerado(self):
        return {letra: [Assento.LIVRE] * qtd for letra, qtd in self.LAYOUT_MESAS.items()}

    def carregar_mesas(self):
        try:
            with open(self._caminho, "r", encoding="utf-8") as arquivo:
                situacao = json.load(arquivo)
        except (FileNotFoundError, json.JSONDecodeError):
            situacao = self._layout_zerado()
            mesas = {letra: Mesa(letra, lista) for letra, lista in situacao.items()}
            self.salvar_mesas(mesas)
            return mesas

        return {letra: Mesa(letra, lista) for letra, lista in situacao.items()}

    def salvar_mesas(self, mesas):
        situacao = {letra: mesa.para_lista_status() for letra, mesa in mesas.items()}
        with open(self._caminho, "w", encoding="utf-8") as arquivo:
            json.dump(situacao, arquivo, ensure_ascii=False)


class Reserva:
    def __init__(self, salao):
        self.salao = salao

    def _imprimir_situacao(self, mesas):
        print("\nSituação atual das mesas:")
        for mesa in mesas.values():
            print(f"  {mesa}")

    def pedir_lugar(self):
        mesas = self.salao.carregar_mesas()
        self._imprimir_situacao(mesas)

        while True:
            entrada_mesa = input(
                "\nDigite uma mesa (A-P) ou 0 para voltar ao menu: "
            ).strip().upper()

            if entrada_mesa == "0":
                return
            if entrada_mesa not in mesas:
                print("Mesa inválida.")
                continue

            mesa = mesas[entrada_mesa]

            while True:
                entrada_numero = input(
                    f"Mesa {mesa.get_letra()} tem {mesa.total_assentos()} assentos. "
                    "Digite o número do assento (0 = menu, 9 = trocar de mesa): "
                )
                try:
                    numero = int(entrada_numero)
                except ValueError:
                    print("Digite um número válido.")
                    continue

                if numero == 0:
                    return
                if numero == 9:
                    break  # volta para escolher outra mesa

                try:
                    assento = mesa.get_assento(numero)
                except ValueError as erro:
                    print(erro)
                    continue

                if not assento.esta_disponivel():
                    print("Esse assento não está disponível.")
                    continue

                assento.set_status(Assento.NO_PAGAMENTO)
                self.salao.salvar_mesas(mesas)
                self.pagamento(mesas, assento)
                return

    # só para a lógica do status do lugar durante o pagamento,
    # depois integramos com o código do pagamento.
    def pagamento(self, mesas, assento):
        while True:
            entrada = input(
                "Forma de pagamento (1-Crédito, 2-Débito, 3-Pix) ou 0 para cancelar: "
            )
            try:
                opcao = int(entrada)
            except ValueError:
                print("Digite um número válido.")
                continue

            if opcao == 0:
                assento.set_status(Assento.LIVRE)
                self.salao.salvar_mesas(mesas)
                print("Reserva cancelada. O assento voltou a ficar livre.")
                return False

            if opcao not in (1, 2, 3):
                print("Opção de pagamento inválida.")
                continue

            assento.set_status(Assento.OCUPADO)
            self.salao.salvar_mesas(mesas)
            print("Pagamento confirmado! Assento reservado.")
            return True

    def exibir(self):
        mesas = self.salao.carregar_mesas()
        self._imprimir_situacao(mesas)

    def menu(self):
        while True:
            print("""
Menu de seleção de lugares!
1 - Escolher lugar
2 - Exibir lugares
3 - Sair""")
            entrada = input("Digite sua opção: ")
            try:
                opcao = int(entrada)
            except ValueError:
                print("Digite um número válido.")
                continue

            if opcao == 1:
                self.pedir_lugar()
            elif opcao == 2:
                self.exibir()
            elif opcao == 3:
                print("Saindo...")
                break
            else:
                print("Valor errado.")


if __name__ == "__main__":
    reserva = Reserva(Salao())
    reserva.menu()
