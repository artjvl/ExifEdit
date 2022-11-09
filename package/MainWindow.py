from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from typing import Optional


class MainWindow(QMainWindow):
    # def __init__(
    #     self,
    #     widget: QWidget,
    #     parent: Optional[QWidget] = None,
    #     flags: Qt.WindowType = None,
    # ) -> None:
    #     super().__init__(parent, flags)

    def __init__(self, widget: QWidget):
        super().__init__()
        self.setWindowTitle("exifedit")
        self._menu = self.menuBar()

        self._file_menu = self._menu.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)
        self._file_menu.addAction(exit_action)

        self.setCentralWidget(widget)

    @Slot()
    def exit_app(self, checked):
        QApplication.quit()
