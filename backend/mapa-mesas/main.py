#retornar 4 valores para banco de dados: cod_lugar, cod_aluno, mesa, ocupado
import json
import os

class Mesas:
    def __init__ (self, mesa, cadeira):
        self.mesa = mesa
        self.cadeira = cadeira
        self.status = 0 #0 == livre; 1 == ocupado; 2 == no pagamento

    lugares_iniciais = {
        'A': [0,0,0,0,0,0,0,0],
        'B': [0,0,0,0,0,0],
        'C': [0,0,0,0,0,0,0,0],
        'D': [0,0,0,0,0,0,0,0],
        'E': [0,0,0,0,0,0,0,0],
        'F': [0,0,0,0,0,0,0,0],
        'G': [0,0,0,0,0,0,0,0],
        'H': [0,0,0,0,0,0],
        'I': [0,0,0,0,0,0],
        'J': [0,0,0,0,0,0],
        'K': [0,0,0,0,0,0],
        'L': [0,0,0,0,0,0],
        'M': [0,0,0,0,0,0],
        'N': [0,0,0,0,0,0],
        'O': [0,0,0,0,0,0],
        'P': [0,0,0,0,0,0,0,0]
    }

    if not os.path.exists("lugares.json"):
        with open("lugares.json", "w", encoding="utf-8") as arq:
            json.dump(lugares_iniciais, arq)


class Reserva:
    def __init__(self, lugares):
        self.lugares = lugares

    def pedir_lugar(self):
        with open("lugares.json", "r", encoding="utf-8") as arq:
            self.lugares = json.load(arq)
            print(self.lugares)
        self.mesa = input("Digite uma mesa (A - P) digite 0 para voltar ao menu: ").strip().upper()
        if self.mesa not in self.lugares:
            print("Mesa inválida")
            return False
        elif self.mesa == "0":
            return False
        self.cadeira = int(input("Digite o número da cadeira (Digite 0 para voltar ao menu e 9 para voltar a página): "))
        self.indice = self.cadeira - 1
        if self.cadeira == 0:
            return False
        elif self.cadeira == 9:
            self.pedir_lugar()
            return
        if self.indice < 0 or self.indice >= len(self.lugares[self.mesa]):
            print("Número inválido de lugar.")
            return False
        if self.lugares[self.mesa][self.indice] == 1:
            print("Esse assento já está ocupado.")
            return False

        self.lugares[self.mesa][self.indice] = 2
        self.status = 2
        with open("lugares.json", "w", encoding="utf-8") as arq:
            json.dump(self.lugares, arq, ensure_ascii=False)
        self.pagamento()

    #só para a lógica do status do lugar durante o pagamento, depois integramos com o código do pagamento.
    def pagamento(self):
        op = int(input("Digite a forma de pagamento: 1 - Crédito | 2 - Débito | 3 - Pix: "))
        self.lugares[self.mesa][self.indice] = 1
        self.status = 1
        with open("lugares.json", "w", encoding="utf-8") as arq:
            json.dump(self.lugares, arq, ensure_ascii=False)
        return True

    def exibir(self):
        with open("lugares.json", "r", encoding="utf-8") as arq:
            self.lugares = json.load(arq)
            print(self.lugares)
            return False

    def menu(self):
        while True:
            print(f"""Menu de seleção de lugares!
            1 - Escolher lugar
            2 - Exibir lugares
            3 - Sair""")
            op = int(input("Digite sua opção: "))
            if op == 1:
                self.pedir_lugar()
            elif op == 2:
                self.exibir()
            elif op == 3:
                break
            else:
                print("Valor errado")

reserva = Reserva(Mesas.lugares_iniciais)
reserva.menu()