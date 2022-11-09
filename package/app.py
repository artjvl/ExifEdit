import sys
from PySide6.QtWidgets import QWidget, QApplication

from package.MainWindow import MainWindow
from package.FileTree import FileTree


def run():
    app = QApplication(sys.argv)
    widget = FileTree()
    window = MainWindow(widget)
    window.resize(800, 600)
    window.show()
    app.exec()
