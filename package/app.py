import sys
from PySide6.QtWidgets import QWidget, QApplication

from package.FileExplorer import FileExplorer
from package.MainWindow import MainWindow


def run():
    app = QApplication(sys.argv)
    widget = FileExplorer()
    window = MainWindow(widget)
    window.resize(800, 600)
    window.show()
    app.exec()
