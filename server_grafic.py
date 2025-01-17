import sys
import socket
from threading import Thread
import pickle
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QTextEdit

class GameRoom:
    def __init__(self, name):
        self.name = name
        self.players = {}
        self.used_cities = []
        self.is_active = False

    def add_player(self, client, player_name):
        self.players[client] = player_name

    def remove_player(self, player, reason=None):
        if player not in self.players:
            return
        name = self.players[player]

        if reason == 'ban':
            self.broadcast(f"{name} был забанен.")
        if reason == 'time_out':
            self.broadcast(f"Время на ответ истекло! {name} не успел ответить!")
        else:
            self.broadcast(f"{name} покинул игру.")

        del self.players[player]
        serialized_data = pickle.dumps({'type': 'end_game'})
        if self.players:
            winner = list(self.players.values())[0]
            winner_sock = list(self.players.keys())[0]
            self.broadcast(f"{winner} победил!")
            winner_sock.send(serialized_data)
        player.send(serialized_data)
        if len(self.players) < 2:
            self.end_game()

    def broadcast(self, message, exclude_client = None):
        for player in self.players:
            if player != exclude_client:
                try:
                    ser_data = pickle.dumps({'type': 'chat', 'body': message})
                    player.send(ser_data)
                except Exception as e:
                    print(f"Error sending message: {e}")

    def start_game(self):
        self.is_active = True
        self.broadcast('Игра началась!')
        serialized_data = pickle.dumps({'type': 'start_game'})
        sock = list(self.players.keys())[0]
        sock.send(serialized_data)

    def end_game(self):
        self.is_active = False
        self.used_cities.clear()
        self.players.clear()

class PlayerThread(Thread):
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
            match data['type']:
                case 'name':
                    self.name = data['body']
                    if self.name in self.server.all_players:
                        if self.server.all_players[self.name]:
                            self.send_pickle({'type': 'ban'})
                    else:
                        self.server.all_players[self.name] = False
                        self.server.players[self.name] = self
                    list_room = [room.name for room in self.server.rooms.values() if not room.is_active and len(room.players) < 2]
                    self.send_pickle({'type': 'rooms', 'body': list_room})

                case 'room':
                    room_name = data['body']
                    if room_name in self.server.rooms:
                        self.room = self.server.rooms[room_name]
                        self.room.add_player(self.sock, self.name)
                        if len(self.room.players) == 2:
                            time.sleep(1)
                            self.room.start_game()
                        else:
                            time.sleep(1)
                            self.send_pickle({'type': 'chat', 'body': "Ожидание второго игрока..."})

                case 'create':
                    room_name = data['body']
                    self.server.create_room(self.name, self.sock, room_name)
                    self.room = self.server.rooms[room_name]
                    time.sleep(1)
                    self.send_pickle({'type': 'chat', 'body': "Ожидание второго игрока..."})

                case 'chat':
                    city = data['body'].strip().lower()
                    if self.check_city(city):
                        self.room.used_cities.append(city)
                        self.send_pickle({'type': 'chat', 'body': f'Ваш город: {city}.'})
                        self.room.broadcast(f"Игрок {self.name} назвал город: {city}.", self.sock)

                case 'exit_room':
                    list_room = [room.name for room in self.server.rooms.values() if
                                 not room.is_active and len(room.players) < 2]
                    self.send_pickle({'type': 'rooms', 'body': list_room})
                    self.room.remove_player(self.sock)

                case 'ban':
                    username = data['body']
                    if username in self.server.all_players:
                        self.server.all_players[username] = True
                        ban_player = self.server.players[username]
                        if ban_player.room:
                            ban_player.room.remove_player(ban_player.sock, 'ban')
                        ser_data = pickle.dumps({'type': 'ban'})
                        ban_player.sock.send(ser_data)

                case 'time_out':
                    self.room.remove_player(self.sock, 'time_out')

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
    def __init__(self, log_callback, host='localhost', port=12345):
        self.log_callback = log_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.rooms = {'RM1': GameRoom('RM1'), 'RM2': GameRoom('RM2'),'RM3': GameRoom('RM3')}
        self.all_players = {}
        self.players = {}
        self.log_message("Сервер запущен и ожидает подключений...")
        self.accept_incoming_connections()

    def log_message(self, message):
        self.log_callback(message)

    def accept_incoming_connections(self):
        while True:
            player, addr = self.server_socket.accept()
            self.log_message(f"Подключился игрок: {addr}")
            PlayerThread(player, addr, self)

    def create_room(self, name, player, room_name):
        if room_name not in self.rooms:
            self.rooms[room_name] = GameRoom(room_name)
        self.rooms[room_name].add_player(player, name)

class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервер")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.start_button = QPushButton("Запустить сервер")
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        self.layout.addWidget(self.start_button)
        self.layout.addWidget(QLabel("Информация с сервера:"))
        self.layout.addWidget(self.text_area)

        self.start_button.clicked.connect(self.start_server)
        self.server_thread = None

    def start_server(self):
        self.server_thread = Thread(target=self.run_server)
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