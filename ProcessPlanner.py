import sys
import time
import threading
from random import randrange
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMessageBox,
    QPushButton,
    QComboBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMainWindow,
    QLineEdit,
    QSpinBox,
    QDialog,
)


class AddProcessWindow(QDialog):
    def __init__(self, parent=None):
        super(AddProcessWindow, self).__init__(parent)
        self.name = ''
        self.priority = 0
        self.initUI()
        self.addButton = QPushButton('Добавить', self)
        self.addButton.setGeometry(120, 150, 80, 30)

    def initUI(self):
        self.setGeometry(500, 400, 480, 200)
        self.setWindowTitle('Добавить процесс')
        self.setInputLine(150, 20, 280, 30, 'Имя процесса')
        self.setSpinBox(150, 70, 50, 30, 'Приоритет')
        self.setPushButton('Отмена', 280, 150, 80, 30, self.close)

    def setInputLine(self, xShift, yShift, width, height, label):
        line = QLineEdit(self)
        line.setGeometry(xShift, yShift, width, height)
        label = QLabel(label, self)
        label.move(xShift - 120, yShift)
        line.textChanged[str].connect(self.onChangeInput)

    def onChangeInput(self, text):
        self.name = text

    def setSpinBox(self, xShift, yShift, width, height, label):
        box = QSpinBox(self)
        box.setGeometry(xShift, yShift, width, height)
        label = QLabel(label, self)
        label.move(xShift - 120, yShift)
        box.valueChanged.connect(self.onChangeSpinBox)

    def onChangeSpinBox(self, value):
        self.priority = value

    def setPushButton(self, title, xShift, yShift, width, height, callback):
        button = QPushButton(title, self)
        button.setGeometry(xShift, yShift, width, height)
        button.clicked.connect(callback)


class ProcessPlanner(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.memory = 0
        self.thread = threading.Thread()
        self.initUI()

    def initUI(self):
        self.move(300, 300)
        self.setFixedSize(1060, 640)
        self.setWindowTitle('Планировщик процессов')

        self.setComboBox(300, 501, 150, 27, '', 'RR', 'ПП невытесняющее')
        self.setTimer(950, 100)
        self.setPushButton('Новый процесс', 100, 500, 120, 30, self.openAddProcessWindow)
        self.setTable(100, 100, 771, 350,
                      'Имя',
                      'Приоритет',
                      'Статус',
                      'Выделение ЦП',
                      'Выделение\nпамяти',
                      'Время\nпоявления',
                      )
        self.show()

    def setTable(self, xShift, yShift, width, height, *columns):
        self.table = QTableWidget(self)
        self.rows = 0
        self.table.setGeometry(xShift, yShift, width, height)
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

    def addRow(self, *headers):
        if self.memory < 100:
            self.rows += 1
            self.table.insertRow(self.rows - 1)
            self.processes.append([headers[1], self.curProcSize, self.curProcSize])
            for i in range(6):
                item = QTableWidgetItem(headers[i])
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(self.rows - 1, i, item)

    def deleteRow(self, row):
        self.rows -= 1
        self.table.removeRow(row)

    def updateRow(self, row, status, cpu):
        statusItem = QTableWidgetItem(status)
        cpuItem = QTableWidgetItem(cpu)
        statusItem.setTextAlignment(Qt.AlignCenter)
        cpuItem.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, statusItem)
        self.table.setItem(row, 3, cpuItem)
        self.table.viewport().update()

    def setPushButton(self, title, xShift, yShift, width, height, callback):
        button = QPushButton(title, self)
        button.setGeometry(xShift, yShift, width, height)
        button.clicked.connect(callback)

    def openAddProcessWindow(self):
        self.curProcSize = randrange(1, 31)
        self.memory += self.curProcSize
        self.window = AddProcessWindow(self)
        self.window.addButton.clicked.connect(self.retrieveProcessData)
        self.window.show()

    def setComboBox(self, xShift, yShift, width, height, *items):
        self.combo = QComboBox(self)
        self.combo.addItems(items)
        self.combo.setGeometry(xShift, yShift, width, height)
        self.combo.activated[str].connect(self.startSwitchMethod)

    def startSwitchMethod(self):
        if not self.thread.isAlive():
            self.thread = threading.Thread(target=self.switchMethod)
            self.thread.start()

    def switchMethod(self):
        while self.isVisible():
            if self.processes:
                if self.combo.currentText() == 'RR':
                    proc = 0
                    while proc < len(self.processes):
                        self.updateRow(proc, 'Выполняется', '100%')
                        if self.processes[proc][1] <= 0:
                            self.updateRow(proc, 'Выполнен', '0%')
                            time.sleep(1)
                            self.deleteRow(proc)
                            self.memory -= self.processes[proc][2]
                            del self.processes[proc]
                            proc -= 1
                        else:
                            self.processes[proc][1] -= 1
                            time.sleep(1)
                            self.updateRow(proc, 'Ожидание', '0%')
                        print(self.processes)
                        proc += 1
                elif self.combo.currentText() == 'ПП невытесняющее':
                    highestProc = self.highestPriority()
                    self.updateRow(highestProc, 'Выполняется', '100%')
                    toPass = False
                    while self.processes[highestProc][1]:
                        if self.combo.currentText() != 'ПП невытесняющее':
                            toPass = True
                            self.updateRow(highestProc, 'Ожидание', '0%')
                            break
                        self.processes[highestProc][1] -= 1
                        print(self.processes)
                        if self.processes[highestProc][1] == 0:
                            self.updateRow(highestProc, 'Выполнен', '0%')
                        time.sleep(1)
                    if toPass:
                        pass
                    else:
                        self.deleteRow(highestProc)
                        self.memory -= self.processes[highestProc][2]
                        del self.processes[highestProc]
                        print(self.processes)

    def highestPriority(self):
        highestProc = 0
        highestPrior = int(self.processes[highestProc][0])
        for i in range(len(self.processes)):
            if int(self.processes[i][0]) > highestPrior:
                highestPrior = int(self.processes[i][0])
                highestProc = i
        return highestProc

    def setTimer(self, xShift, yShift):
        self.timer = QLabel(time.strftime('%H:%M:%S', (1, 1, 1, 0, 0, 0, 1, 1, 1)), self)
        self.timer.move(xShift, yShift)
        self.h = 0
        self.m = 0
        self.s = 0
        self.timerID = self.startTimer(1000)

    def showTime(self):
        self.curTime = time.strftime('%H:%M:%S', (1, 1, 1, self.h, self.m, self.s, 1, 1, 1))
        self.timer.setText(self.curTime)

    def timerEvent(self, event):
        if self.s == 59:
            self.s = 0
            if self.m == 59:
                self.m = 0
                self.h += 1
            else:
                self.m += 1
        else:
            self.s += 1
        self.showTime()

    def retrieveProcessData(self):
        if self.memory < 100:
            process = [self.window.name, self.window.priority, self.curProcSize]
            self.window.close()
            self.addRow(process[0], str(process[1]), 'Ожидание', '0%', str(process[2]) + '%', str(self.curTime))
            print(self.processes)
        else:
            self.window.close()
            self.window = QMessageBox(self)
            self.window.setIcon(QMessageBox.Critical)
            self.window.setText('Память переполнена!')
            self.window.setWindowTitle('Ошибка')
            self.memory -= self.curProcSize
            self.window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProcessPlanner()
    sys.exit(app.exec_())
