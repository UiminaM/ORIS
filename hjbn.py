import socket
import pickle
from threading import Thread
from queue import SimpleQueue
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QIcon, QFont
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QInputDialog,\
    QVBoxLayout, QTextEdit, QLineEdit, QMainWindow, QLabel, QComboBox, QMessageBox
from PyQt6 import QtGui

class Communication(QObject):
    chat_signal = pyqtSignal(str)
    game_signal = pyqtSignal(int, int, str)
    start_game_signal = pyqtSignal()
    end_game_signal = pyqtSignal()
    timer_signal = pyqtSignal(int)
class BeginingWindow(QWidget):  # начальное окно
    def __init__(self):
        super().__init__()

        # Настройка шрифта
        font = QFont("Noteworthy", 14)
        #Noteworthy Yuppy TC
        self.communication = Communication()
        self.sock_comm = Socket('127.0.0.1', 12345, self.communication)

        # Настройка размеров окна
        self.setGeometry(250, 250, 600, 480)
        self.setFixedSize(600, 480)

        # Основная метка
        self.main_label = QLabel(self)
        pixmap = QtGui.QPixmap('title.jpg')  # Замените на путь к вашему изображению
        self.main_label.setPixmap(pixmap)
        self.main_label.setGeometry(100, 40, 380, 80)  # Установите размеры и положение метки
        self.main_label.setScaledContents(True)

        # Комбо-бокс для выбора размера поля
        self.choice = QComboBox(self)
        self.choice.addItems(["3 x 3", "5 x 5", "7 x 7"])
        self.choice.setCurrentIndex(1)
        self.choice.setGeometry(100, 240, 150, 31)

        # Метка для выбора поля
        self.label = QLabel(self)
        self.label.setText('Выберите поле для игры:')
        self.label.setGeometry(100, 210, 200, 20)

        # Установка шрифта для меток и полей ввода
        self.label.setFont(font)

        # Метки и поля ввода для имен игроков
        self.name1 = QLabel(self)
        self.name1.setText('Имя первого игрока:')
        self.name1.setGeometry(340, 180, 150, 20)
        self.name1.setFont(font)

        self.vvod1 = QLineEdit(self)
        self.vvod1.setGeometry(340, 210, 160, 30)
        self.vvod1.setStyleSheet('background-color: #FEFDF5')

        self.name2 = QLabel(self)
        self.name2.setText('Имя второго игрока:')
        self.name2.setGeometry(340, 260, 150, 20)
        self.name2.setFont(font)

        self.vvod2 = QLineEdit(self)
        self.vvod2.setGeometry(340, 290, 160, 30)
        self.vvod2.setStyleSheet('background-color: #FEFDF5')

        # Кнопка для начала игры
        self.play = QPushButton(self)
        self.play.setGeometry(180, 390, 250, 50)
        self.play.setText('Начать игру')
        self.play.setStyleSheet('background-color: #FFCFB1')
        self.play.setFont(font)  # Установка шрифта для кнопки

        # Настройка стиля
        self.setStyleSheet('background-color: #ffedcc')
        self.choice.setStyleSheet("QComboBox{color: black; background-color: white;}")

        self.show()
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

if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    window = BeginingWindow()
    app.exec()