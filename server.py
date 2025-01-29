import socket
import sqlite3
from threading import Thread
import pickle
import random
from queue import SimpleQueue


class GameRoom:
    def __init__(self, players, first_word):
        self.players = players
        self.used_words = []
        self.first_word = first_word
        self.create_field(first_word)

        self.p_counts = [0, 0]
        self.p_words = {0: [], 1: []}
        self.current_player = 0

        self.start_game()

    def start_game(self):
        body = list(self.players.keys())
        body.append(self.first_word)
        self.broadcast('start_game', body)

    def create_field(self, word):
        self.field = [[None for j in range(len(word))] for i in range(len(word))]
        for x in range(len(word)):
            for y in range(len(word)):
                if x == len(word)// 2:
                     self.field[x][y] = word[y]

    def broadcast(self, type, message="", exclude_client=None):
        for player in list(self.players.values()):
            if player != exclude_client:
                try:
                    ser_data = pickle.dumps({'type': type, 'body': message})
                    player.send(ser_data)
                except Exception as e:
                    print(f"Error sending message: {e}")

    def game_over(self):
        if all(letter is not None for x in self.field for letter in x):
            self.broadcast('game_over', [self.p_counts, self.p_words])



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
        con = sqlite3.connect("data/dic3.db")
        cur = con.cursor()
        con2 = sqlite3.connect("data/ozhigov.db")
        cur2 = con2.cursor()

        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            data = pickle.loads(data)
            match data['type']:
                case 'user':
                    self.name, self.field = data['body']
                    self.server.fields[str(self.field)].queue.put(self)

                case 'word':
                    word = data['body'][0]
                    new_letter = data['body'][1:]

                    if word in self.room.p_words[0] or word in self.room.p_words[1] or word == self.room.first_word:
                        self.send_pickle({'type': 'guide', 'body': 'Такое слово уже было!\nПридумайте новое.'})
                    elif self.check_word(word, cur, cur2):
                        self.send_pickle({'type': 'end_timer'})
                        self.room.p_counts[self.room.current_player] += len(word)  # обновление счета
                        self.room.p_words[self.room.current_player].append(word)  # списка слов
                        self.get_description(word.lower(), cur2)  # значение последнего слова
                        self.room.current_player = 1 - self.room.current_player
                        self.room.broadcast('player_change', [self.room.p_counts, self.room.p_words])
                        self.room.field[new_letter[1]][new_letter[2]] = new_letter[0]
                        self.room.broadcast('new_letter', new_letter, self.sock)
                        self.room.broadcast(type='start_timer', exclude_client=self.sock)
                        self.room.game_over()
                    else:
                        self.send_pickle({'type': 'guide', 'body': 'Слово не найдено в словаре!\nПопробуйте ввести другое.'})

                case 'pass_move':
                    self.send_pickle({'type': 'end_timer'})
                    self.room.p_words[self.room.current_player].append('-')
                    self.room.current_player = 1 - self.room.current_player
                    self.room.broadcast('player_change', [self.room.p_counts, self.room.p_words])
                    self.room.broadcast(type='start_timer', exclude_client=self.sock)
        con.close()
        con2.close()


    def send_pickle(self, data):
        serialized_data = pickle.dumps(data)
        self.sock.send(serialized_data)

    def check_word(self, word, cur, cur2):
        result = cur.execute("""SELECT * FROM words
                    WHERE word = ?""", (word,)).fetchone()  # поиск слова в морфологическом словаре
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                    WHERE word = ?""", (word.lower(),)).fetchone()  # поиск слова в толковом словаре
        if result or result_2:  # нет ли слова в уже введенных и есть ли в нем последняя буква
            return True
        return False

    def get_description(self, word, cur2):  # добавление определения слова
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                               WHERE word = ?""", (word.lower(),)).fetchone()
        if result_2:
            des = ' '.join(str(result_2[2][2:]).split('\\n'))[:1020]
            self.room.broadcast('description', des)
        else:
            self.room.broadcast('description', 'Определение слова отсутсвует в толковом словаре.')

class Field(Thread):
    def __init__(self, size):
        super().__init__()
        self.queue = SimpleQueue()
        match size:
            case 3:
                self.words = ["ДАР"]
            case 5:
                self.words = ["СПОРТ", "ТОПОР", "ЛАСКА"]
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
        self.sock.bind((host, port))
        self.sock.listen()
        print('Сервер запущен...')

        self.fields = {"3": Field(3), "5": Field(5), "7": Field(7)}

    def start_server(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            print(f"Подключен клиент: {client_addr}")
            ClientThread(client_sock, client_addr, self)


if __name__ == "__main__":
    server = Server(host='127.0.0.1', port=12345)
    server.start_server()

