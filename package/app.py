import sys
from PySide6.QtWidgets import QWidget, QApplication

from package.ExifEdit import ExifEdit
from package.MainWindow import MainWindow


def run():
    app = QApplication(sys.argv)
    widget = ExifEdit()
    window = MainWindow(widget)
    window.resize(920, 920)
    window.show()
    app.exec()
