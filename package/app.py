import sys
from PySide6.QtWidgets import QApplication

from package.MainWindow import MainWindow


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
