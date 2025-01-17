import socket
import re
import pickle
from queue import SimpleQueue
from threading import Thread
from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QInputDialog, QVBoxLayout, QTextEdit, QLineEdit, QMainWindow, QLabel, QComboBox, QMessageBox

class GUICommunication(QObject):
    start_signal = pyqtSignal()
    end_signal = pyqtSignal()
    chat_updating_signal = pyqtSignal(str)
    ban_signal = pyqtSignal()
    room_updating_signal = pyqtSignal(list)

class Socket(QObject):
    def __init__(self, host, port, gui_communication):
        super().__init__()
        self.queue = SimpleQueue()
        self.gui_communication = gui_communication
        self.rooms = ['RM1', 'RM2', 'RM3']
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

        Thread(target=self.send_data, daemon=True).start()
        Thread(target=self.receive_data, daemon=True).start()

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    continue
                message = pickle.loads(data)
                type = message['type']

                if type == 'chat':
                    self.gui_communication.chat_updating_signal.emit(message['body'])
                elif type == 'ban':
                    self.gui_communication.ban_signal.emit()
                elif type == 'rooms':
                    self.rooms = message['body']
                    self.gui_communication.room_updating_signal.emit(self.rooms)
                elif type == 'start_game':
                    self.gui_communication.start_signal.emit()
                elif type == 'end_game':
                    self.gui_communication.end_signal.emit()
                else:
                    continue
            except Exception as e:
                print(f"Error1: {e, type}")
                break

    def send_data(self):
        while True:
            try:
                data = self.queue.get()
                serialized_data = pickle.dumps(data)
                self.client_socket.send(serialized_data)
            except Exception as e:
                print(f"Error2: {e}")
                break

class BanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('БАН')
        self.setGeometry(100, 100, 400, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        self.ban_message_label = QLabel("Вы забанены, дальнейшая игра недоступна.", self)
        layout.addWidget(self.ban_message_label)
        central_widget.setLayout(layout)

class UserNameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('АВТОРИЗАЦИЯ')
        self.setGeometry(100, 100, 400, 200)
        layout = QVBoxLayout()

        self.gui_communication = GUICommunication()
        self.client = Socket('127.0.0.1', 12345, self.gui_communication)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Введите ваше имя")
        layout.addWidget(self.username_input)

        self.enter_button = QPushButton("Войти", self)
        layout.addWidget(self.enter_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.enter_button.clicked.connect(self.open_main_window)
        self.main_room_window = None

    @pyqtSlot()
    def open_main_window(self):
        name = self.username_input.text()
        if name:
            self.client.queue.put({'type': 'name', 'body': name})
            self.main_room_window = MainRoomWindow(name, self.client, self.gui_communication)
            self.main_room_window.show()
            self.hide()

class MainRoomWindow(QMainWindow):
    def __init__(self, name, client, gui_communication):
        super().__init__()
        self.client = client
        self.gui_communication = gui_communication

        self.setWindowTitle('ОСНОВНАЯ КОМНАТА')
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.greeting_label = QLabel(self)
        layout.addWidget(self.greeting_label)
        self.set_greeting(name)

        self.rooms_combo_box = QComboBox(self)
        self.rooms_combo_box.addItems(self.client.rooms)
        layout.addWidget(self.rooms_combo_box)

        self.enter_room_button = QPushButton('Войти в комнату', self)
        layout.addWidget(self.enter_room_button)

        self.create_room_button = QPushButton('Создать комнату', self)
        layout.addWidget(self.create_room_button)

        self.exit_button = QPushButton('Выход', self)
        layout.addWidget(self.exit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.enter_room_button.clicked.connect(self.open_chat_window)
        self.create_room_button.clicked.connect(self.create_room)

        self.exit_button.clicked.connect(self.exit_app)
        self.gui_communication.room_updating_signal.connect(self.update_rooms)
        self.gui_communication.ban_signal.connect(self.ban)
    def set_greeting(self, username):
        self.greeting_label.setText(f"Привет, {username}!")


    def update_rooms(self, rooms):
        self.rooms_combo_box.clear()
        self.rooms_combo_box.addItems(rooms)

    @pyqtSlot()
    def open_chat_window(self):
        cur_room = self.rooms_combo_box.currentText()
        if cur_room:
            self.client.queue.put({'type': 'room', 'body': cur_room})
            self.game_window = GameWindow(self.client, cur_room, self)
            self.game_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите комнату для входа.")

    @pyqtSlot()
    def create_room(self):
        room_name, ok = QInputDialog.getText(self, 'Создать комнату', 'Введите имя комнаты:')
        if ok and room_name:
            self.client.queue.put({'type': 'create', 'body': room_name})
            self.game_window = GameWindow(self.client, room_name, self)
            self.game_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Ошибка", "Имя комнаты не может быть пустым.")

    @pyqtSlot()
    def exit_app(self):
        self.close()

    @pyqtSlot()
    def ban(self):
        self.ban_window = BanWindow()
        self.ban_window.show()
        self.hide()


class GameWindow(QMainWindow):
    def __init__(self, client, room_name, main_window: MainRoomWindow):
        super().__init__()
        self.client = client
        self.main_window = main_window

        self.setWindowTitle(f"КОМНАТА - {room_name}")
        self.setGeometry(100, 100, 600, 400)
        self.setFixedSize(600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.time_out)
        self.timer.setSingleShot(True)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText('Введите сообщение...')
        layout.addWidget(self.input_line)

        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.exit_room_button = QPushButton("Покинуть комнату")
        self.exit_room_button.clicked.connect(self.exit_room)
        layout.addWidget(self.exit_room_button)

        self.ban_player_button = QPushButton("Забанить игрока")
        self.ban_player_button.clicked.connect(self.ban_player)
        layout.addWidget(self.ban_player_button)

        central_widget.setLayout(layout)

        self.main_window.gui_communication.chat_updating_signal.connect(self.update_chat)
        self.main_window.gui_communication.ban_signal.connect(self.ban)
        self.main_window.gui_communication.start_signal.connect(self.start)
        self.main_window.gui_communication.end_signal.connect(self.end_game)

    @pyqtSlot()
    def start(self):
        self.text_edit.append('Ваш ход. Введите город:')
        self.send_button.setEnabled(True)
        self.timer.start(30000)

    @pyqtSlot()
    def end_game(self):
        self.timer.stop()
        self.send_button.setEnabled(False)
        self.text_edit.append("Игра окончена! Будет совершен автоматический переход в основнуйю комнату через 10 секунд.")

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.exit_room)
        self.timer2.setSingleShot(True)
        self.timer2.start(10000)

    def send_message(self):
        message = self.input_line.text()
        if message:
            self.client.queue.put({'type': 'chat', 'body': message})
            self.input_line.clear()

    @pyqtSlot()
    def time_out(self):
        self.client.queue.put({'type': 'time_out'})

    @pyqtSlot()
    def exit_room(self):
        self.client.queue.put({'type': 'exit_room'})
        self.main_window.gui_communication.ban_signal.disconnect()
        self.main_window.update_rooms(self.client.rooms)
        self.main_window.show()
        self.hide()

    @pyqtSlot()
    def ban_player(self):
        player_name, ok = QInputDialog.getText(self, 'Забанить игрока', 'Введите имя игрока для бана:')
        if ok and player_name:
            self.client.queue.put({'type': 'ban', 'body': player_name})


    def update_chat(self, data):
        self.text_edit.append(data)
        if re.search(r'Ваш город', data):
            self.send_button.setEnabled(False)
            self.timer.stop()
        if re.search(r'назвал город', data):
            self.text_edit.append('Ваш ход. Введите город:')
            self.send_button.setEnabled(True)
            self.timer.start(30000)

    @pyqtSlot()
    def ban(self):
        self.ban_window = BanWindow()
        self.ban_window.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication([])
    user_name_window = UserNameWindow()
    user_name_window.show()
    app.exec()