import copy
import socket
import pickle
from threading import Thread
from queue import SimpleQueue
from PyQt6.QtGui import QBrush, QColor, QPainter, QFont, QPen
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer, QSize, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, \
    QVBoxLayout, QLineEdit, QMainWindow, QLabel, QComboBox, QGridLayout, \
    QTableWidget, QHeaderView, QTableWidgetItem, QPlainTextEdit, QHBoxLayout
from PyQt6 import QtGui

STATUSES = {0: 'Выберите букву и вставьте ее \nв свободную клетку.',
            1: 'Покажите слово от первой \nдо последней буквы.'}


class Communication(QObject):
    guide_signal = pyqtSignal(str)
    start_game_signal = pyqtSignal(list, str)
    game_over_signal = pyqtSignal(list, dict)
    description_signal = pyqtSignal(str)
    player_change_signal = pyqtSignal(list, dict)
    new_letter_signal = pyqtSignal(list)
    timer_signal = pyqtSignal()
    end_timer_signal = pyqtSignal()
    error_signal = pyqtSignal()

class Socket(QObject):
    def __init__(self, host, port, communication):
        super().__init__()
        self.queue = SimpleQueue()
        self.communication = communication
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

        Thread(target=self.send_data, daemon=True).start()
        Thread(target=self.receive_data, daemon=True).start()

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(2500)
                if not data:
                    continue
                message = pickle.loads(data)
                type = message['type']
                print(type)
                if type == 'guide':
                    print(message['body'])
                    self.communication.guide_signal.emit(message['body'])
                elif type == 'start_game':
                    print(message['body'])
                    names = message['body'][:2]
                    word = message['body'][-1]
                    self.communication.start_game_signal.emit(names, word)
                elif type == 'description':
                    print(message['body'])
                    self.communication.description_signal.emit(message['body'])
                elif type == 'new_letter':
                    print(message['body'])
                    self.communication.new_letter_signal.emit(message['body'])
                elif type == 'start_timer':
                    self.communication.timer_signal.emit()
                elif type == 'end_timer':
                    self.communication.end_timer_signal.emit()
                elif type == 'game_over':
                    p_count, p_words = message['body']
                    self.communication.game_over_signal.emit(p_count, p_words)
                elif type == 'player_change':
                    print(message['body'])
                    p_count, p_words = message['body']
                    self.communication.player_change_signal.emit(p_count, p_words)
                else:
                    continue
            except Exception:
                self.communication.error_signal.emit()
                break

    def send_data(self):
        while True:
            try:
                data = self.queue.get()
                serialized_data = pickle.dumps(data)
                self.client_socket.send(serialized_data)
            except Exception:
                self.communication.error_signal.emit()
                break


class BeginingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.communication = Communication()
        self.socket = Socket('127.0.0.1', 12348, self.communication)

        self.setGeometry(100, 100, 480, 380)
        self.setFixedSize(480, 360)
        font = QFont("Yuppy TC", 14)
        font_error = QFont("Yuppy TC", 11)
        self.setStyleSheet('background-color: #ffedcc')

        self.main_label = QLabel(self)
        pixmap = QtGui.QPixmap('title.jpg')
        self.main_label.setPixmap(pixmap)
        self.main_label.setGeometry(100, 40, 280, 55)
        self.main_label.setScaledContents(True)

        self.name1 = QLabel(self)
        self.name1.setText('Введите имя:')
        self.name1.setGeometry(140, 125, 140, 20)
        self.name1.setFont(font)

        self.lineEdit = QLineEdit(self)
        self.lineEdit.setGeometry(140, 150, 200, 30)
        self.lineEdit.setStyleSheet('background-color: #FEFDF5')

        self.label = QLabel(self)
        self.label.setText('Выберите поле для игры:')
        self.label.setGeometry(140, 195, 200, 20)
        self.label.setFont(font)

        self.choice = QComboBox(self)
        self.choice.addItems(["3 x 3", "5 x 5", "7 x 7"])
        self.choice.setCurrentIndex(1)
        self.choice.setGeometry(140, 220, 200, 31)
        self.choice.setStyleSheet("QComboBox{color: black; background-color: white;}")

        self.play = QPushButton(self)
        self.play.setGeometry(140, 270, 200, 40)
        self.play.setText('Начать игру')
        self.play.setStyleSheet('background-color: #fcc1a9')
        self.play.setFont(font)

        self.error = QLabel(self)
        self.error.setGeometry(140, 310, 200, 20)
        self.error.setFont(font_error)

        self.play.clicked.connect(self.check)

    @pyqtSlot()
    def check(self):
        if self.lineEdit.text() == '':
            self.error.setText('Имя не может быть пустым!')
        else:
            name = self.lineEdit.text()
            field = int(self.choice.currentText()[0])
            self.socket.queue.put({'type': 'user', 'body': [name, field]})
            self.wait_window = WaitWindow(name, self.communication, self.socket, field, self)
            self.hide()


class WaitWindow(QWidget):
    def __init__(self, name, communication, socket, field, begin_window):
        super().__init__()
        self.name = name
        self.communication = communication
        self.begin_window = begin_window
        self.socket = socket
        self.field = field
        self.setGeometry(100, 100, 350, 200)
        self.setFixedSize(350, 200)
        self.setStyleSheet('background-color: #ffedcc')

        self.main_label = QLabel(self)
        pixmap = QtGui.QPixmap('title.jpg')
        self.main_label.setPixmap(pixmap)
        self.main_label.setGeometry(35, 40, 280, 55)
        self.main_label.setScaledContents(True)

        self.inscription = QLabel(self)
        self.inscription.setText('Поиск второго игрока...')
        self.inscription.setGeometry(40, 120, 280, 40)
        self.inscription.setFont(QFont("Yuppy TC", 20))

        self.communication.start_game_signal.connect(self.open_game_window)
        self.show()

    def open_game_window(self, players, word):
        window.__init__(players, self.name, self.socket, self.field, word, self.communication, self.begin_window)
        window.show()
        self.hide()


class Cell(QWidget):
    def __init__(self, x, y, f):
        super(Cell, self).__init__()

        self.setFixedSize(QSize(400 // f, 400 // f))

        self.is_filled = False
        self.move_fill = False
        self.is_letter = False
        self.letter = None
        self.x = x
        self.y = y

    def set_letter(self, letter):
        if not self.is_letter and letter:
            self.is_letter = True
            self.letter = letter
            self.update()

    def reset(self):
        self.is_filled = False
        self.letter = None
        self.is_letter = False
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = [QColor('#97C5D8'), QColor('#FFB180')]
        r = event.rect()

        if self.is_filled or self.move_fill:
            color = colors[window.current_player]
            outer, inner = QColor(0, 0, 0), color
        else:
            outer, inner = QColor(0, 0, 0), QColor('#FEFDF5')

        qp.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        qp.setPen(pen)
        qp.drawRect(r)

        if self.is_letter:
            qp.setPen(QColor(0, 0, 0))
            qp.setFont(QFont('Yuppy TC', 30))
            qp.drawText(r, Qt.AlignmentFlag.AlignCenter, self.letter)

    def enterEvent(self, e):
        self.move_fill = True
        self.update()

    def leaveEvent(self, e):
        self.move_fill = False
        window.update()

    def highlighting(self):
        if self.is_letter:
            if len(window.current_word) > 0:
                comp_cell = window.current_word[len(window.current_word) - 1]
                if self not in window.current_word and ((comp_cell.x == self.x and abs(self.y - comp_cell.y) == 1) or (
                        comp_cell.y == self.y and abs(self.x - comp_cell.x) == 1)):
                    window.current_word.append(self)
                    self.is_filled = True
            else:
                window.current_word.append(self)
                self.is_filled = True
            self.update()

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton) and window.game_status == STATUSES[0]:
            if not self.is_letter and window.remembered_alphabit_letter.text() and window.field.check_heighbor_cells(
                    self):
                self.set_letter(window.remembered_alphabit_letter.text())
                window.field.last_letter = self
                self.update()
                window.game_status = STATUSES[1]
                window.set_guide()
        elif window.game_status == STATUSES[1]:
            if (e.button() == Qt.MouseButton.LeftButton):
                self.highlighting()
                print('highlighting')
            elif (e.button() == Qt.MouseButton.LeftButton):
                if self.is_filled and self == window.current_word[len(window.current_word) - 1]:
                    window.current_word = window.current_word[:len(window.current_word) - 1]
                    self.is_filled = False
                    self.update()
                if not window.current_word and self == window.field.last_letter:
                    window.delete_letter()
        window.set_guide()


class Field(QWidget):
    def __init__(self, word, field):
        super(Field, self).__init__()
        self.f_size = field
        self.word = word
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.setLayout(self.grid)
        self.grid.setHorizontalSpacing(0)
        self.orig_cells_objects = [[None for j in range(self.f_size)] for i in range(self.f_size)]
        self.last_letter = None
        self.init_map()
        self.cells_objects = copy.copy(self.orig_cells_objects)
        self.setMaximumSize(420, 420)

    def init_map(self):
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                a = Cell(x, y, self.f_size)
                if x == self.f_size // 2:
                    a.set_letter(self.word[y])
                self.grid.addWidget(a, x, y)
                self.orig_cells_objects[x][y] = a

    def reset_map(self):
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                self.cells_objects[x][y].is_filled = False

    def check_heighbor_cells(self, cell):
        if cell.x > 0:
            if self.cells_objects[cell.x - 1][cell.y].is_letter:
                return True
        if cell.y > 0:
            if self.cells_objects[cell.x][cell.y - 1].is_letter:
                return True
        if cell.x < 4:
            if self.cells_objects[cell.x + 1][cell.y].is_letter:
                return True
        if cell.y < 4:
            if self.cells_objects[cell.x][cell.y + 1].is_letter:
                return True
        return False


class GameWindow(QMainWindow):
    def __init__(self, players=['player1', 'player2'], name='', socket=None, field=0, word='', communication=None,
                 begin_window: BeginingWindow = None):
        super().__init__()
        self.socket = socket
        self.name = name
        self.communication = communication
        self.begin_window = begin_window
        self.players = players
        self.field_size = field
        self.first_word = word
        self.remembered_alphabit_letter = None
        self.current_word = []
        self.game_status = STATUSES[0]
        self.current_player = 0

        self.setWindowTitle(self.name)
        self.field = Field(self.first_word, self.field_size)
        self.setGeometry(50, 100, 800, 600)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setMaximumSize(self.width() // 2, 250)
        self.table.setHorizontalHeaderLabels(self.players)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.word_description = QPlainTextEdit(self)
        self.word_description.setReadOnly(True)
        self.word_description.setMaximumSize(self.width() // 2, 250)

        self.counts = QLabel(self)
        self.counts.setText(str('0 : 0'))
        self.counts.setFont(QFont('Arial', 30))

        self.guide_label = QLabel()
        self.now_move = QLabel(self)
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        self.now_move.setFont(QFont("Arial", 20))

        self.delete_letter_btn = QPushButton(self)
        self.delete_letter_btn.setText('Удалить букву')
        self.delete_letter_btn.setMinimumSize(100, 50)
        self.delete_letter_btn.setEnabled(False)
        self.delete_letter_btn.clicked.connect(self.delete_letter)

        self.delete_word_btn = QPushButton(self)
        self.delete_word_btn.setText('Удалить слово')
        self.delete_word_btn.setMinimumSize(100, 50)
        self.delete_word_btn.setEnabled(False)
        self.delete_word_btn.clicked.connect(self.delete_word)

        self.add_word_btn = QPushButton(self)
        self.add_word_btn.setMinimumSize(100, 50)
        self.add_word_btn.clicked.connect(self.make_a_move)

        self.pass_move_btn = QPushButton(self)
        self.pass_move_btn.setText('Пропустить ход')
        self.pass_move_btn.setMinimumSize(100, 50)
        self.pass_move_btn.clicked.connect(self.pass_move)

        self.new_game_btn = QPushButton(self)
        self.new_game_btn.setText('Начать новую игру')
        self.new_game_btn.setMinimumSize(100, 50)
        self.new_game_btn.clicked.connect(self.back_begin_window)
        self.new_game_btn.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.pass_move)
        self.timer.setSingleShot(True)

        self.main_vb = QVBoxLayout()
        self.upper_hb = QHBoxLayout()
        self.table_vb = QVBoxLayout()
        self.btn_vb = QVBoxLayout()
        self.game_field_vb = QVBoxLayout()
        self.count_hb = QHBoxLayout()
        self.count_hb.addStretch(1)
        self.count_hb.addWidget(self.counts)
        self.count_hb.addStretch(1)

        self.main_vb.addLayout(self.upper_hb)
        self.upper_hb.addLayout(self.game_field_vb)
        self.game_field_vb.addStretch(1)
        self.game_field_vb.addWidget(self.field)
        self.game_field_vb.addStretch(1)
        self.upper_hb.addStretch(1)
        self.upper_hb.addLayout(self.btn_vb)
        self.upper_hb.addStretch(1)
        self.btn_vb.addWidget(self.now_move)
        self.btn_vb.addWidget(self.guide_label)
        self.btn_vb.addWidget(self.add_word_btn)
        self.btn_vb.addWidget(self.delete_letter_btn)
        self.btn_vb.addWidget(self.delete_word_btn)
        self.btn_vb.addWidget(self.pass_move_btn)
        self.upper_hb.addLayout(self.table_vb)
        self.table_vb.addLayout(self.count_hb)
        self.table_vb.addWidget(self.table)
        self.table_vb.addWidget(self.word_description)

        self.table.setStyleSheet('background-color: #FEFDF5')
        self.word_description.setStyleSheet('background-color: #FEFDF5')
        self.sp = list(self.findChildren(QPushButton))
        font = QFont("Arial", 14)
        for x in self.sp:
            x.setFont(font)
            x.setStyleSheet('background-color: #fcc1a9')

        central_widget = QWidget(self)
        central_widget.setLayout(self.main_vb)
        central_widget.setStyleSheet('background-color: #ffedcc')
        self.setCentralWidget(central_widget)

        self.init_alphabit()
        self.set_guide()
        if self.communication != None:
            self.communication.player_change_signal.connect(self.player_change)
            self.communication.guide_signal.connect(self.set_error)
            self.communication.description_signal.connect(self.set_description)
            self.communication.new_letter_signal.connect(self.add_new_letter)
            self.communication.timer_signal.connect(self.start_timer)
            self.communication.end_timer_signal.connect(self.end_timer)
            self.communication.game_over_signal.connect(self.game_over)
            self.communication.error_signal.connect(self.open_error_window)

    def init_alphabit(self):
        alp = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        a = QWidget(self)
        a.grid = QGridLayout()
        a.grid.setSpacing(0)
        a.setLayout(a.grid)
        for x in range(0, 3):
            for y in range(0, 11):
                new = QPushButton(self)
                new.setText(alp[x * 11 + y])
                new.setMinimumSize(0, 20)
                font = QFont("Yuppy TC", 14)
                font.setPointSize(20)
                font.setWeight(20)
                new.setFont(font)
                new.setStyleSheet('background-color: #faeccd')
                new.clicked.connect(self.alphabit_letter_is_pressed)
                a.grid.addWidget(new, x, y)

        self.main_vb.addWidget(a)

    def alphabit_letter_is_pressed(self):
        if self.remembered_alphabit_letter:
            self.remembered_alphabit_letter.setStyleSheet('background-color: #faeccd')
        self.remembered_alphabit_letter = self.sender()
        self.sender().setStyleSheet('background-color: #FF9A5C')

    def set_guide(self):
        self.guide_label.setText(self.game_status)
        self.guide_label.setFont(QFont('Arial', 14))
        if self.game_status == STATUSES[0] or self.game_status == STATUSES[1]:
            self.add_word_btn.hide()
        if self.game_status == STATUSES[1]:
            self.delete_letter_btn.setEnabled(True)
            if self.current_word:
                self.add_word_btn.show()
                self.add_word_btn.setText(''.join([x.letter for x in self.current_word]))
                self.delete_word_btn.setEnabled(True)  \

    def set_error(self, text):
        self.guide_label.setText(text)
        self.guide_label.update()
        self.delete_word()

    def set_description(self, des):
        self.word_description.setPlainText(des)
        self.word_description.update()

    def add_new_letter(self, new_letter):
        print('add_new_letter')
        self.field.orig_cells_objects[new_letter[1]][new_letter[2]].set_letter(new_letter[0])

    def update_table(self, p_words):
        self.table.setRowCount(len(p_words[0]))
        self.table.setItem(len(p_words[0]) - 1, self.current_player,
                           QTableWidgetItem(p_words[self.current_player][len(p_words[0]) - 1]))

    def start_timer(self):
        self.timer.start(30000)

    def end_timer(self):
        self.timer.stop()

    def make_a_move(self):
        if self.game_status == STATUSES[1]:
            word = ''.join(j.letter for j in self.current_word)
            if self.field.last_letter not in self.current_word:
                self.set_error('Слово должно содержать новую букву!')
            else:
                self.socket.queue.put({'type': 'word',
                                       'body': [word, self.field.last_letter.letter, self.field.last_letter.x,
                                                self.field.last_letter.y]})


    def player_change(self, p_counts, p_words):
        self.update_table(p_words)
        self.counts.setText(str(p_counts[0]) + ' : ' + str(p_counts[1]))
        self.current_player = 1 - self.current_player
        self.field.last_letter = None
        self.delete_word()
        self.field.orig_cells_objects = self.field.cells_objects
        if self.remembered_alphabit_letter:
            self.remembered_alphabit_letter.setStyleSheet('background-color: #faeccd')
            self.remembered_alphabit_letter = None
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        self.delete_letter_btn.setEnabled(False)
        self.game_status = STATUSES[0]
        self.set_guide()

    def delete_letter(self):
        self.field.last_letter.reset()
        self.game_status = STATUSES[0]
        self.delete_word()
        self.set_guide()
        self.delete_letter_btn.setEnabled(False)

    def delete_word(self):
        self.current_word = []
        self.field.reset_map()
        self.field.update()
        self.add_word_btn.hide()
        self.delete_word_btn.setEnabled(False)

    def pass_move(self):
        if self.field.last_letter:
            self.delete_letter()
        self.socket.queue.put({'type': 'pass_move'})

    def game_over(self, p_counts, p_words):
        if p_counts[0] == p_counts[1]:
            text = 'Ничья!'
        else:
            winner = p_counts.index(max(p_counts))
            text = 'Поздравляем, ' + self.players[winner] + '!\nВы победили!'
        self.now_move.setText(text)
        the_best_word = max(p_words[0] + p_words[1], key=len)  # определение самого длинного слова
        self.guide_label.setText(f'\nЛучшее слово за игру:\n{the_best_word}')
        self.delete_word_btn.hide()  # убираем ненужные кнопки
        self.delete_letter_btn.hide()
        self.add_word_btn.hide()
        self.pass_move_btn.hide()
        self.btn_vb.addWidget(self.new_game_btn)
        self.new_game_btn.show()

    def back_begin_window(self):
        self.begin_window.show()
        self.hide()

    def open_error_window(self):
        self.err_window = ErrorWindow()
        self.hide()


class ErrorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 350, 200)
        self.setFixedSize(350, 200)
        self.setStyleSheet('background-color: #ffedcc')

        self.main_label = QLabel(self)
        pixmap = QtGui.QPixmap('title.jpg')
        self.main_label.setPixmap(pixmap)
        self.main_label.setGeometry(35, 40, 280, 55)
        self.main_label.setScaledContents(True)

        self.inscription = QLabel(self)
        self.inscription.setText('Соединение с сервером потеряно...')
        self.inscription.setGeometry(40, 120, 280, 40)
        self.inscription.setFont(QFont("Yuppy TC", 16))

        self.show()


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    window = GameWindow()
    b_window = BeginingWindow()
    b_window.show()
    app.exec()