import socket
import threading
import pickle
from concurrent.futures import ThreadPoolExecutor
import os

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
                print(f"Ошибка при отправке сообщения: {e}")
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
                    self.broadcast(f"Игрок {self.names[current_player]} отключился. ")
                    self.players[current_player].send("end".encode())
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
                self.broadcast(f"Игрок {name} забанен.")
                self.players[self.names.index(name)].send("end".encode())
                self.players[self.names.index(name)].close()
                self.remove_player(self.names.index(name))
                break
            current_player = 1 - current_player
        self.broadcast(f"Ожидание другого игрока...")
        self.isActive = True

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
    def __init__(self, host='localhost', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.count_rooms = 0
        self.rooms = {}
        self.all_players = {}
        print("Сервер запущен и ожидает подключения...")
        self.accept_incoming_connections()

    def accept_incoming_connections(self):
        with ThreadPoolExecutor() as executor:
            while True:
                client, addr = self.server_socket.accept()
                print(f"Подключен клиент: {addr}")
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
        free_rooms = [room_id for room_id, room in self.rooms.items() if len(room.players) < 2 and room.isActive]
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

if __name__ == "__main__":
    server = Server()