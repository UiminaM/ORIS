import copy
import socket
import pickle
import random
from threading import Thread
from queue import SimpleQueue
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QIcon, QFont, QPen
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer, QSize, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QInputDialog, \
    QVBoxLayout, QTextEdit, QLineEdit, QMainWindow, QLabel, QComboBox, QMessageBox, QGridLayout, \
    QTableWidget, QHeaderView, QTableWidgetItem, QPlainTextEdit, QHBoxLayout, QLayout
from PyQt6 import QtGui

ALPHABIT = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
STATUSES = {0: 'Выберите букву и вставьте ее \nв свободную клетку.',
            1: 'Покажите слово от первой \nдо последней буквы. Для отмены \nнажмите правой кнопкой мыши.',
            2: 'Конец игры.'}
class Communication(QObject):
    chat_signal = pyqtSignal(str)
    game_signal = pyqtSignal(int, int, str)
    start_game_signal = pyqtSignal()
    end_game_signal = pyqtSignal()
    timer_signal = pyqtSignal(int)
class BeginingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.communication = Communication()
        self.socket = Socket('127.0.0.1', 12345, self.communication)

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

        self.show()

    @pyqtSlot()
    def check(self):
        if self.lineEdit.text() == '':
            self.error.setText('Имя не может быть пустым!')
        else:
            name = self.lineEdit.text()
            field = int(self.choice.currentText()[0])
            self.socket.queue.put({'type': 'name', 'body': name})
            self.socket.queue.put({'type': 'size', 'body': name})
            window.__init__(name, self.socket, field, self)
            window.show()
            self.hide()

class GameWindow(QMainWindow):
    def __init__(self, name="", socket=None, field=0, begin_window: BeginingWindow=None):
        super().__init__()
        self.socket = socket
        self.begin_window = begin_window
        self.players = [name, 'player2']
        self.field_size = field  # размер поля
        self.remembered_alphabit_letter = None  # последняя выбранная из алфавита буква
        self.current_word = []  # текущее набираемое слово
        self.game_status = STATUSES[0]  # текущий статус игры
        self.current_player = 0  # чей ход
        self.p_counts = [0, 0]  # счет игры
        self.p_words = {0: [], 1: []}  # все веденные слова

        self.field = Field(self.generate_word(), self.field_size)  # создание поля
        self.setGeometry(100, 100, 900, 700)


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
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        font2 = QtGui.QFont('Yuppy TC', 30)
        self.counts.setFont(font2)

        # Надписи и кнопки
        self.guide_label = QLabel()
        self.now_move = QLabel(self)
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        font3 = QtGui.QFont('Yuppy TC', 20)
        self.now_move.setFont(font3)

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
        self.new_game_btn.setText('Начать заново')
        self.new_game_btn.setMinimumSize(100, 50)
        self.new_game_btn.clicked.connect(self.close)
        self.new_game_btn.hide()

        self.main_vb = QVBoxLayout()
        self.upper_hb = QHBoxLayout()
        self.table_vb = QVBoxLayout()
        self.btn_vb = QVBoxLayout()
        self.game_field_vb = QVBoxLayout()
        self.count_hb = QHBoxLayout()
        self.count_hb.addWidget(self.counts)

        self.main_vb.addLayout(self.upper_hb)
        self.upper_hb.addLayout(self.game_field_vb)
        self.game_field_vb.addStretch(1)
        self.game_field_vb.addWidget(self.field)
        self.game_field_vb.addStretch(1)
        self.upper_hb.addLayout(self.btn_vb)
        self.btn_vb.addWidget(self.now_move)
        self.btn_vb.addWidget(self.guide_label)
        self.btn_vb.addWidget(self.add_word_btn)
        self.btn_vb.addWidget(self.delete_letter_btn)
        self.btn_vb.addWidget(self.delete_word_btn)
        self.btn_vb.addWidget(self.pass_move_btn)
        self.upper_hb.addLayout(self.table_vb)
        self.table_vb.addLayout(self.count_hb)
        self.table_vb.addWidget(self.table)
        self.table_vb.addWidget(self.word_description)2

        self.setStyleSheet('background-color: #EBF0F7')
        self.table.setStyleSheet('background-color: #FEFDF5')
        self.word_description.setStyleSheet('background-color: #FEFDF5')
        self.sp = list(self.findChildren(QPushButton))
        for x in self.sp:
            x.setStyleSheet('background-color: #FFCFB1')

        central_widget = QWidget(self)
        central_widget.setLayout(self.main_vb)
        self.setCentralWidget(central_widget)

        self.init_alphabit()  # Создание алфавита
        self.set_guide()  # Установка надписи-руководства
        self.setFont(QtGui.QFont('Yuppy TC', 12))

    def init_alphabit(self):  # алфавит
        a = QWidget(self)  # Create a new QWidget to hold the alphabet buttons
        a.grid = QGridLayout()  # Create a new QGridLayout
        a.grid.setSpacing(0)
        a.setLayout(a.grid)  # Set the layout for the new widget
        for x in range(0, 3):
            for y in range(0, 11):
                new = QPushButton(self)
                new.setText(ALPHABIT[x * 11 + y])
                new.setMinimumSize(0, 50)
                font = QtGui.QFont()
                font.setPointSize(20)
                font.setWeight(50)
                new.setFont(font)
                new.clicked.connect(self.alphabit_letter_is_pressed)  # Connect button click
                a.grid.addWidget(new, x, y)  # Add button to the grid layout

        self.main_vb.addWidget(a)

    def alphabit_letter_is_pressed(self):
        if self.remembered_alphabit_letter:  # убираем выделение с последней запомненной буквы
            self.remembered_alphabit_letter.setStyleSheet('background-color: #FFCFB1')
        self.remembered_alphabit_letter = self.sender()  # запоминаем последнюю введенную букву
        self.sender().setStyleSheet('background-color: #FF9A5C')

    def generate_word(self):  # с помощью словаря-базы данных выбираем случайное слово для начала игры

        return "карта"

    def set_guide(self):
        self.guide_label.setText(self.game_status)
        if self.game_status == STATUSES[0] or self.game_status == STATUSES[1]:
            self.add_word_btn.hide()  # прячем "ввести слово", если еще не выделена буква
        if self.game_status == STATUSES[1]:
            self.delete_letter_btn.setEnabled(True)  # доступ к кнопке - удалению буквы
            if self.current_word:
                self.add_word_btn.show()  # показываем "ввести слово", если выделена хоть одна буква
                self.add_word_btn.setText(''.join([x.letter for x in self.current_word]))
                self.delete_word_btn.setEnabled(True)  # доступ к кнопке - удалению слова

    def make_a_move(self):  # проверяет и делает ход
        if self.game_status == STATUSES[1]:
            word = ''.join(j.letter for j in self.current_word)  # введенное слово
            if self.check_word(word):  # если прошло проверку
                self.p_counts[self.current_player] += len(word)  # обновление счета
                self.p_words[self.current_player].append(word)  # списка слов
                self.set_description(word.lower())  # значение последнего слова
                self.player_change()  # меняем игрока
                self.game_over()  # проверка на окончание игры
            else:  # слово не прошло проверку
                if self.field.last_letter not in self.current_word:
                    text = 'Слово должно содержать новую букву!'
                elif word in self.p_words[0] or word in self.p_words[1] or word == self.first_word:
                    text = 'Такое слово уже было!\nПридумайте новое.'
                else:
                    text = 'Извините, данного слова нет в \nсловаре. Попробуйте ввести другое.'
                self.guide_label.setText(text)
                self.guide_label.update()
                self.delete_word()
    def check_word(self, word):  # проверка слова
        global cur
        result = cur.execute("""SELECT * FROM words
                    WHERE word = ?""", (word,)).fetchone()  # поиск слова в морфологическом словаре
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                    WHERE word = ?""", (word.lower(),)).fetchone()  # поиск слова в толковом словаре
        if (result or result_2) and word not in self.p_words[0] and word not in self.p_words[
            1] and word != self.first_word and self.field.last_letter in self.current_word:  # нет ли слова в уже введенных и есть ли в нем последняя буква
            return True
        return False

    def update_table(self):  # обновление таблицы слов
        self.table.setRowCount(len(self.p_words[0]))
        self.table.setItem(len(self.p_words[0]) - 1, self.current_player,
                           QTableWidgetItem(self.p_words[self.current_player][len(self.p_words[0]) - 1]))

    def player_change(self):  # смена игрока
        if not self.current_word:
            self.p_words[self.current_player].append('-')  # если пропускает ход
        self.update_table()
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        if self.current_player == 0:  # смена номера игрока
            self.current_player = 1
        else:
            self.current_player = 0
        self.field.last_letter = None  # сброс промежуточных введений
        self.delete_word()
        self.field.orig_cells_objects = self.field.cells_objects  # обновляем массив клеток
        self.remembered_alphabit_letter.setStyleSheet('background-color: #ffcfb1')  # сброс выделения в алфавите
        self.remembered_alphabit_letter = None
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        self.delete_letter_btn.setEnabled(False)
        self.game_status = STATUSES[0]
        self.set_guide()

    def delete_letter(self):  # сброс введенной буквы
        self.field.last_letter.reset()
        self.game_status = STATUSES[0]
        self.delete_word()
        self.set_guide()
        self.delete_letter_btn.setEnabled(False)

    def delete_word(self):  # сброс вводимого слова
        self.current_word = []
        self.field.reset_map()
        self.field.update()
        self.add_word_btn.hide()
        self.delete_word_btn.setEnabled(False)

    def pass_move(self):  # пропуск хода
        if self.field.last_letter:
            self.delete_letter()
        self.player_change()

    def set_description(self, word):  # добавление определения слова
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                               WHERE word = ?""", (word.lower(),)).fetchone()
        if result_2:
            des = ' '.join(str(result_2[2][2:]).split('\\n'))
            self.word_description.setPlainText(des)
        else:
            self.word_description.setPlainText('Извините, данное слово отсутсвует в толковом словаре.')

    def game_over(self):  # проверка и действие при окончании игры
        if all(z.is_letter for z in [self.field.orig_cells_objects[x][y] for x in range(self.field_size) for y in
                                     range(self.field_size)]):  # не осталось свободных клеток
            if self.p_counts[0] == self.p_counts[1]:
                text = 'Ничья!'
            else:
                winner = self.p_counts.index(max(self.p_counts))
                text = 'Поздравляем, ' + self.players[winner] + '!\nВы победили!'
            self.now_move.setText('')
            self.guide_label.setText('\tКонец игры.')
            self.the_best_word = max(self.p_words[0] + self.p_words[1], key=len)  # определение самого длинного слова
            text += '\nЛучшее слово за игру:\n' + self.the_best_word
            #nt = Congratulations(text)  # поздравительное окошко
            #self.btn_vb.insertWidget(0, nt)
            self.btn_vb.removeWidget(self.now_move)
            self.delete_word_btn.hide()  # убираем ненужные кнопки
            self.delete_letter_btn.hide()
            self.add_word_btn.hide()
            self.pass_move_btn.hide()
            self.btn_vb.addWidget(self.new_game_btn)
            self.new_game_btn.show()  # добавляем кнопку для новой игры (закрытия старой)
            self.game_status = STATUSES[2]


class Field(QWidget):  # класс игрового поля
    def __init__(self, word, field):
        super(Field, self).__init__()
        self.f_size = field  # размер (сколько на сколько ячеек)
        self.word = word  # изначальное слово (по середине)
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.setLayout(self.grid)
        self.grid.setHorizontalSpacing(0)
        self.orig_cells_objects = [[None for j in range(self.f_size)] for i in range(self.f_size)]  # массив клеток
        self.last_letter = None
        self.init_map()
        self.cells_objects = copy.copy(self.orig_cells_objects)  # промежуточный массив клеток
        self.setMaximumSize(520, 520)

    def init_map(self):  # создание поля
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                a = Cell(x, y, self.f_size)
                if x == self.f_size // 2:
                    a.set_letter(self.word[y])
                self.grid.addWidget(a, x, y)
                self.orig_cells_objects[x][y] = a

    def reset_map(self):  # сброс поля
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                self.cells_objects[x][y].is_filled = False

    def check_heighbor_cells(self, cell):  # проверяет, есть ли рядом с выбранной клеткой другие с буквами
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

class Cell(QWidget):  # класс для клеток с буквами
    def __init__(self, x, y, f):
        super(Cell, self).__init__()

        self.setFixedSize(QSize(500 // f, 500 // f))

        self.is_filled = False  # закрашена (выбрана)
        self.move_fill = False  # закрашена из-за наведения мышкой
        self.is_letter = False  # есть ли буква внутри
        self.letter = None  # какая буква

        self.x = x  # координаты на сетке клеток (класс Field)
        self.y = y

    def set_letter(self, letter):  # для установки буквы в клетку
        if not self.is_letter and letter:
            self.is_letter = True
            self.letter = letter
            self.update()

    def reset(self):  # приводит к первоначальному (стандартному) виду
        self.is_filled = False
        self.letter = None
        self.is_letter = False
        self.update()

    def paintEvent(self, event):  # функция отрисовки клетки
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = [QColor('#97C5D8'), QColor('#FFB180')]
        r = event.rect()

        if self.is_filled or self.move_fill:  # закрашивается при наведении или выделении (нажатии)
            color = colors[window.current_player]
            outer, inner = QColor(0, 0, 0), color
        else:
            outer, inner = QColor(0, 0, 0), QColor('#FEFDF5')  # Use QColor for black

        qp.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        qp.setPen(pen)
        qp.drawRect(r)

        if self.is_letter:  # вставить букву
            qp.setPen(QColor(0, 0, 0))
            qp.setFont(QFont("Arial", 30))
            qp.drawText(r, Qt.AlignmentFlag.AlignCenter, self.letter)

    def enterEvent(self, e):  # наведение мышкой в область клетки (для закрашивания)
        self.move_fill = True
        self.update()

    def leaveEvent(self, e):  # выход мышки из области клетки
        self.move_fill = False
        window.update()

    def highlighting(self):  # проверяет, можно ли выбрать клетку (если есть буква и она рядом с другими выделенными)
        if self.is_letter:
            if len(window.current_word) > 0:
                comp_cell = window.current_word[len(window.current_word) - 1]
                if self not in window.current_word and ((comp_cell.x == self.x and abs(self.y - comp_cell.y) == 1) or (
                        comp_cell.y == self.y and abs(self.x - comp_cell.x) == 1)):
                    window.current_word.append(self)
                    self.is_filled = True
            else:
                window.current_word.append(self)  # добавляет букву в конец вводимого слова
                self.is_filled = True
            self.update()

    def mousePressEvent(self, e):  # варианты при нажатии
        if (e.button() == Qt.MouseButton.LeftButton) and window.game_status == STATUSES[0]:  # вставление буквы
            if not self.is_letter and window.remembered_alphabit_letter.text() and window.field.check_heighbor_cells(
                    self):
                self.set_letter(window.remembered_alphabit_letter.text())  # вставляет выбранную из алфавита букву
                window.field.last_letter = self
                self.update()
                window.game_status = STATUSES[1]
                window.set_guide()
        elif window.game_status == STATUSES[1]:
            if (e.button() == Qt.MouseButton.LeftButton):  # выделение клетки (добавление буквы к текущему слову)
                self.highlighting()
            if (e.button() == Qt.MouseButton.LeftButton):  # удаление клетки из текущего слова
                if self.is_filled and self == window.current_word[len(window.current_word) - 1]:
                    window.current_word = window.current_word[:len(window.current_word) - 1]
                    self.is_filled = False
                    self.update()
                if not window.current_word and self == window.field.last_letter:  # удаление буквы из клетки
                    window.delete_letter()

        window.set_guide()
class Socket(QObject):
    def __init__(self, host, port, gui_communication):
        super().__init__()
        self.queue = SimpleQueue()
        self.gui_communication = gui_communication
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
    window = GameWindow()
    window2 = BeginingWindow()
    app.exec()