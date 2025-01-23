import socket
from threading import Thread
import pickle
import struct
from queue import SimpleQueue
import time

class GameRoom:
    def __init__(self, players):
        self.players = players
        self.used_words = []
        self.broadcast('start_game', list(players.keys()))

    def broadcast(self, type, message="", exclude_client=None):
        for player in list(self.players.values()):
            if player != exclude_client:
                try:
                    ser_data = pickle.dumps({'type': type, 'body': message})
                    player.send(ser_data)
                except Exception as e:
                    print(f"Error sending message: {e}")

    def end_game(self):
        self.used_words.clear()
        self.players.clear()

class ClientThread(Thread):
    def __init__(self, sock, addr, server):
        super().__init__()
        self.sock = sock
        self.addr = addr
        self.server = server
        self.name = ''
        self.room = None
        self.start()

    def run(self):
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            data = pickle.loads(data)
            print(data['type'])
            match data['type']:
                case 'user':
                    self.name, self.field = data['body']
                    self.server.fields[str(self.field)].queue.put(self)

    def send_pickle(self, data):
        serialized_data = pickle.dumps(data)
        self.sock.send(serialized_data)

    def check_city(self, city):
        if city in self.room.used_cities:
            self.send_pickle({"type": "chat", "body": "Этот город уже был назван, повторите попытку:"})
            return False
        elif self.room.used_cities and self.room.used_cities[-1][-1] != city[0]:
            self.send_pickle({"type": "chat", "body": "Неверный ввод, повторите попытку:"})
            return False
        return True
class Field(Thread):
    def __init__(self, size):
        super().__init__()
        self.queue = SimpleQueue()
        match size:
            case 3:
                self.words = ["кот", "дом", "мир", "сок", "лес", "топ", "шум", "пес", "дар", "сто", "мир", "зло"]
            case 5:
                self.words = ["кошка", "книга", "птица", "кнопка", "доска", "карта", "спорт", "топор", "ласка"]
            case 7:
                self.words = ["парашют", "планета", "счетчик"]
        self.start()
    def run(self):
        while True:
            if self.queue.qsize() >= 2:
                client1 = self.queue.get()
                client2 = self.queue.get()
                GameRoom({client1.name: client1.sock, client2.name: client2.sock})


class Server:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen()
        print('Сервер запущен...')

        self.fields = {"3": Field(3), "5":Field(5), "7": Field(7)}

    def serve_forever(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            print(f"Подключен клиент: {client_addr}")
            ClientThread(client_sock, client_addr, self)

if __name__ == "__main__":
    server = Server(host='127.0.0.1', port=12348)
    server.serve_forever()