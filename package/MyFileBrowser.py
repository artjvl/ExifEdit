from PySide6 import QtWidgets, QtCore


class MyFileBrowser(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._tree_view = QtWidgets.QTreeView()
        self.setCentralWidget(self._tree_view)
        self.populate()

    def populate(self):
        model = QtWidgets.QFileSystemModel()
        model.setRootPath(QtCore.QDir.rootPath())
        model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        self._tree_view.setModel(model)
        self._tree_view.setSortingEnabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    fb = MyFileBrowser()
    fb.show()
    app.exec()
