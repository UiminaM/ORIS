import socket
from threading import Thread
import pickle
import struct
import time

class PlayerThread(Thread):
    def __init__(self, sock, addr):
        super().__init__()
        self.sock = sock
        self.addr = addr
        self.name = ''
        self.room = None
        self.start()

    def run(self):
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            data = pickle.loads(data)
            match data['type']:
                case 'name':
                    self.name = data['body']
                    if self.name in self.server.all_players:
                        if self.server.all_players[self.name]:
                            self.send_pickle({'type': 'ban'})
                    else:
                        self.server.all_players[self.name] = False
                        self.server.players[self.name] = self
                    list_room = [room.name for room in self.server.rooms.values() if
                                 not room.is_active and len(room.players) < 2]
                    self.send_pickle({'type': 'rooms', 'body': list_room})

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

class Server:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen()
        print('Сервер запущен...')

    def serve_forever(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            print(f"Подключен клиент: {client_addr}")
            #client_thread = ClientThread(client_sock, client_addr, self.rooms)

if __name__ == "__main__":
    server = Server(host='127.0.0.1', port=12345)
    server.serve_forever()