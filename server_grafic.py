import sys
import socket
import threading
import pickle
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QTextEdit

class GameRoom:
    def __init__(self, server):
        self.players = []
        self.names = []
        self.used_cities = []
        self.isActive = True
        self.server = server

    def add_player(self, name, player):
        self.names.append(name)
        self.players.append(player)

    def remove_player(self, player):
        del self.players[player]
        del self.names[player]

    def broadcast(self, message):
        for player in self.players:
            try:
                player.send(message.encode())
            except Exception as e:
                self.server.log_message(f"Ошибка при отправке сообщения: {e}")
                continue

    def game(self):
        current_player = 0
        name = self.names[current_player]
        self.broadcast(f"Игра началась! {self.names[current_player]}, твой ход.")

        while self.isActive and len(self.players) == 2:
            player = self.players[current_player]
            timer = threading.Timer(30, lambda: self.end_of_time(current_player))
            timer.start()
            while True:
                player.send("Введите город: ".encode())
                city = player.recv(1024).decode().strip()
                if city.lower() == 'exit':
                    self.broadcast(f"Игрок {self.names[current_player]} отключился.")
                    self.players[current_player].close()
                    self.remove_player(current_player)
                    self.isActive = False
                    break
                elif city.lower() == 'change':
                    self.broadcast(f"Игрок {self.names[current_player]} вышел из комнаты.")
                    self.server.add_in_room(self.names[current_player], self.players[current_player])
                    self.remove_player(current_player)
                    self.isActive = False
                    break
                elif city.lower().split()[0] == 'ban':
                    name = city.lower().split()[1]
                    if name in self.server.all_players.keys():
                        self.server.all_players[city.lower().split()[1]] = True
                        self.server.save_players(self.server.all_players)
                        if name in self.names:
                            break
                    else:
                        self.broadcast("Введенный игрок не найден")
                elif self.check_city(city):
                    self.used_cities.append(city)
                    self.broadcast(f"{self.names[current_player]}: {city}")
                    break
                else:
                    player.send("Неправильный ввод, попробуйте снова.\n".encode())

            timer.cancel()

            if not self.isActive:
                break

            elif self.server.all_players[name]:
                self.players[self.names.index(name)].send(f"Вы были забанены".encode())
                self.players[1-self.names.index(name)].send(f"Игрок {name} забанен.".encode())
                self.players[self.names.index(name)].close()
                self.remove_player(self.names.index(name))
                break
            current_player = 1 - current_player
        self.broadcast(f"Ожидание другого игрока...")
        self.isActive = True
        while len(self.players) == 1:
            command = self.players[0].recv(1024).decode().strip()
            if command.lower() == 'exit':
                self.players[0].close()
                self.remove_player(0)
                self.isActive = False
                break
            elif command.lower() == 'change':
                self.server.add_in_room(self.names[0], self.players[0])
                self.remove_player(0)
                self.isActive = False
                break
            elif command.lower().split()[0] == 'ban':
                name = command.lower().split()[1]
                if name in self.server.all_players.keys():
                    self.server.all_players[city.lower().split()[1]] = True
                    self.server.save_players(self.server.all_players)
                else:
                    self.broadcast("Введенный игрок не найден")


    def check_city(self, city):
        if city in self.used_cities:
            return False
        if len(self.used_cities) > 0 and city[0].lower() != self.used_cities[-1][-1].lower():
            return False
        return True

    def end_of_time(self, current_player):
        self.broadcast(
            f"Игрок {self.names[current_player]} не ответил вовремя. Игра окончена. Победитель: {self.names[1 - current_player]}.")
        self.end_game()

    def end_game(self):
        self.isActive = False
        for player in self.players:
            player.send("end".encode())
            player.close()
        self.players.clear()
        self.names.clear()
        self.used_cities.clear()


class Server:
    def __init__(self, log_callback, host='localhost', port=12361):
        self.log_callback = log_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.count_rooms = 0
        self.rooms = {}
        self.all_players = {}
        self.log_message("Сервер запущен и ожидает подключения...")
        self.accept_incoming_connections()

    def log_message(self, message):
        self.log_callback(message)

    def accept_incoming_connections(self):
        with ThreadPoolExecutor() as executor:
            while True:
                client, addr = self.server_socket.accept()
                self.log_message(f" Подключен клиент: {addr}")
                name = client.recv(1024).decode()
                all_players = {}
                with open('players.pkl', 'rb') as file:
                    all_players = pickle.load(file)

                if name in all_players.keys():
                    if not all_players[name]:
                        executor.submit(self.change_mode, name, client)
                    else:
                        client.send(f"Вы забанены и не можете начать игру".encode())
                else:
                    self.all_players[name] = False
                    self.save_players(self.all_players)
                    executor.submit(self.change_mode, name, client)

    def change_mode(self, name, client):
        client.send(
            f"Добро пожаловать в игру, {name}!\n1 - Создать новую игру\n2 - Присоединиться к существующей игре".encode())
        mode = client.recv(1024).decode()
        if mode == '1':
            self.create_room(name, client)
        elif mode == '2':
            self.add_in_room(name, client)

    def create_room(self, name, client):
        self.count_rooms += 1
        self.rooms[self.count_rooms] = GameRoom(self)
        self.rooms[self.count_rooms].add_player(name, client)
        client.send("Ожидание второго игрока...".encode())

    def add_in_room(self, name, client):
        free_rooms = [room_id for room_id, room in self.rooms.items() if len(room.players) < 2 and room.isActive and room.players[0] != client]
        if len(free_rooms) == 0:
            client.send(f"Свободные комнаты отсутствуют. Ожидайте второго игрока в новой комнате\n".encode())
            self.create_room(name, client)
        else:
            client.send(f"Выберите одну из свободных комнат: {', '.join(map(str, free_rooms))}".encode())
            num_room = int(client.recv(1024).decode())
            if num_room in self.rooms:
                self.rooms[num_room].add_player(name, client)
                threading.Thread(target=self.rooms[num_room].game).start()
            else:
                client.send("Комната не найдена или заполнена.\n".encode())

    def save_players(self, all_players):
        with open('players.pkl', 'wb') as file:
            pickle.dump({name: status for name, status in all_players.items()}, file)

class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Server")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.start_button = QPushButton("Start Server")
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        self.layout.addWidget(self.start_button)
        self.layout.addWidget(QLabel("Messages from the server:"))
        self.layout.addWidget(self.text_area)


        self.start_button.clicked.connect(self.start_server)
        self.server_thread = None

    def start_server(self):
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()

    def run_server(self):
        self.server = Server(self.message)
    def message(self, message):
        self.text_area.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerGUI()
    window.show()
    sys.exit(app.exec())