from PySide6 import QtWidgets, QtCore, QtGui


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, widget: QtWidgets.QWidget):
        super().__init__()
        self.setWindowTitle("exifedit")
        self._menu = self.menuBar()

        self._file_menu = self._menu.addMenu("File")
        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)
        self._file_menu.addAction(exit_action)

        self.setCentralWidget(widget)

    @QtCore.Slot()
    def exit_app(self, checked):
        QtWidgets.QApplication.quit()
