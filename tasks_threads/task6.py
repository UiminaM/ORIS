import threading
import random
import time


class Bank:
    def __init__(self, balance):
        self.balance = balance
        self.condition = threading.Condition()

    def withdraw(self, amount):
        with self.condition:
            while self.balance < amount:
                print(f"Недостаточно средств для снятия {amount}. Остаток: {self.balance}. Ожидайте пополнения...")
                self.condition.wait()
            self.balance -= amount

    def top_up(self, amt):
        with self.condition:
            self.balance += amt
            print(f"Баланс пополнен на {amt}. Текущий баланс: {self.balance}.")
            self.condition.notify_all()


class Client(threading.Thread):
    def __init__(self, bank, name):
        threading.Thread.__init__(self)
        self.bank = bank
        self.name = name

    def run(self):
        withdrawal_amount = random.randint(100, 600)
        print(f"{self.name} пытается снять {withdrawal_amount}.")
        self.bank.withdraw(withdrawal_amount)
        print(f"{self.name} успешно снял {withdrawal_amount}. Остаток на счете: {self.bank.balance}.")
        time.sleep(random.uniform(0.5, 1.5))

        top_up_amount = random.randint(100, 600)
        print(f"{self.name} пополняет баланс на {top_up_amount}.")
        self.bank.top_up(top_up_amount)


n = int(input("Введите число клиентов банка: "))
summy = int(input("Введите баланс банка: "))

bank = Bank(summy)
clients = []

for i in range(n):
    client = Client(bank, f"Клиент {i + 1}")
    clients.append(client)

for client in clients:
    client.start()

for client in clients:
    client.join()
