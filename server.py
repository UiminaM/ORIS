import socket
import sqlite3
from threading import Thread
import pickle
import random
from queue import SimpleQueue
import time


class GameRoom:
    def __init__(self, players, first_word):
        self.players = players
        self.used_words = []
        self.first_word = first_word
        self.create_field(first_word)

        self.p_counts = [0, 0]  # счет игры
        self.p_words = {0: [], 1: []}  # все веденные слова
        self.current_player = 0

        body = list(self.players.keys())
        body.append(first_word)
        self.broadcast('start_game', body)

    def create_field(self, word):
        self.field = [['' for j in range(len(word))] for i in range(len(word))]

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
        # Создаем соединение и курсор в этом потоке
        con = sqlite3.connect("data/dic3.db")
        cur = con.cursor()
        con2 = sqlite3.connect("data/ozhigov.db")
        cur2 = con2.cursor()

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
                case 'word':
                    word = data['body'][0]
                    print(word+'1')
                    new_letter = data['body'][1:]

                    if word in self.room.p_words[0] or word in self.room.p_words[1] or word == self.room.first_word:
                        self.send_pickle({'type': 'guide', 'body': 'Такое слово уже было!\nПридумайте новое.'})

                    elif self.check_word(word, cur, cur2):
                        self.room.p_counts[self.room.current_player] += len(word)  # обновление счета
                        self.room.p_words[self.room.current_player].append(word)  # списка слов
                        self.get_description(word.lower(), cur2)  # значение последнего слова
                        self.room.current_player = 1 - self.room.current_player
                        self.room.broadcast('player_change', [self.room.p_counts, self.room.p_words])
                        self.room.broadcast('new_letter', new_letter, self.sock)
                        #self.game_over()
                    else:
                        self.send_pickle({'type': 'guide', 'body': 'Попробуйте ввести другое.'})

                case 'pass_move':
                    self.room.p_words[self.room.current_player].append('-')
                    self.room.current_player = 1 - self.room.current_player
                    self.room.broadcast('player_change', [self.room.p_counts, self.room.p_words])


        con.close()
        con2.close()

    def send_pickle(self, data):
        serialized_data = pickle.dumps(data)
        self.sock.send(serialized_data)
    def check_word(self, word, cur, cur2):
        result = cur.execute("""SELECT * FROM words
                    WHERE word = ?""", (word,)).fetchone()  # поиск слова в морфологическом словаре
        print("in check_word")
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                    WHERE word = ?""", (word.lower(),)).fetchone()  # поиск слова в толковом словаре
        print(f"in check_word: {result}, {result_2}")
        if result or result_2:  # нет ли слова в уже введенных и есть ли в нем последняя буква
            return True
        return False

    def get_description(self, word, cur2):  # добавление определения слова
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                               WHERE word = ?""", (word.lower(),)).fetchone()
        if result_2:
            des = ' '.join(str(result_2[2][2:]).split('\\n'))
            self.room.broadcast('description', des)
        else:
            self.room.broadcast('description', 'Данное слово отсутсвует в толковом словаре.')

class Field(Thread):
    def __init__(self, size):
        super().__init__()
        self.queue = SimpleQueue()
        match size:
            case 3:
                self.words = ["КОТ", "ДОМ", "МИР", "СОК", "ЛЕС", "ТОП", "ШУМ", "ПЕС", "ДАР", "СТО", "МИР", "ЗЛО"]
            case 5:
                self.words = ["КОШКА", "КНИГА", "ПТИЦА", "ДОСКА", "КАРТА", "СПОРТ", "ТОПОР", "ЛАСКА"]
            case 7:
                self.words = ["ПАРАШЮТ", "ПЛАНЕТА", "СЧЕТЧИК"]
        self.start()
    def run(self):
        while True:
            if self.queue.qsize() >= 2:
                client1 = self.queue.get()
                client2 = self.queue.get()
                game_room = GameRoom({client1.name: client1.sock, client2.name: client2.sock}, random.choice(self.words))
                client1.room = game_room
                client2.room = game_room

class Server:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen()
        print('Сервер запущен...')

        self.fields = {"3": Field(3), "5": Field(5), "7": Field(7)}

    def serve_forever(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            print(f"Подключен клиент: {client_addr}")
            ClientThread(client_sock, client_addr, self)  # Передаем курсоры в поток клиента


if __name__ == "__main__":
    server = Server(host='127.0.0.1', port=12348)
    server.serve_forever()

