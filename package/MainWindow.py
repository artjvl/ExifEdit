from typing import Optional, List, Tuple
from PySide6 import QtCore, QtWidgets, QtGui

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer
from package.FileEdit import FileEdit
from package.Image import Image
from package.FileModify import FileModify


class MainWindow(QtWidgets.QMainWindow):

    _SIZE: Tuple[int, int] = (920, 920)

    _file_tree: FileTree
    _file_list: FileList
    _image_viewer: ImageViewer
    _file_edit: FileEdit
    _file_modify: FileModify

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ExifEdit")
        self.setFixedSize(*self._SIZE)
        settings: QtCore.QSettings = QtCore.QSettings("ArtvL", "ExifEdit")

        # widgets - file-tree
        self._file_tree: FileTree = FileTree(settings, parent=self)

        # widgets - file-list
        self._file_list: FileList = FileList(parent=self)
        self._file_tree.signal_path_changed.connect(
            self.on_folder
        )  # dependency: file-list
        self._file_tree.load_settings()

        # widgets - image-viewer
        self._image_viewer: ImageViewer = ImageViewer(parent=self)
        self._file_list.signal_selection_changed.connect(
            self.on_images
        )  # dependency: image-viewer
        self._image_viewer.signal_image_changed.connect(
            self.on_image
        )  # dependency: file-edit

        # widgets - file-edit
        self._file_edit: FileEdit = FileEdit(settings, parent=self)

        # widgets - file-modify
        self._file_modify: FileModify = FileModify(self._file_edit, parent=self)
        self._file_modify.signal_done.connect(
            self.on_modify
        )  # dependencies: file-tree, file-list, file-edit

        # layouts
        widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self.setCentralWidget(widget)

        layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._file_tree)
        layout.addWidget(self._file_list)

        action_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        action_layout.addWidget(self._image_viewer)
        frame: QtWidgets.QFrame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.HLine)
        frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        action_layout.addWidget(frame)
        action_layout.addWidget(self._file_edit)
        action_layout.addStretch()
        action_layout.addWidget(self._file_modify)

        layout.addItem(action_layout)
        widget.setLayout(layout)

        # menus
        self._menu = self.menuBar()

        # menu - file
        self._file_menu = self._menu.addMenu("File")
        action_exit: QtGui.QAction = QtGui.QAction("Exit", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.exit_app)
        self._file_menu.addAction(action_exit)
        action_send2trash: QtGui.QAction = QtGui.QAction(
            "Send original file copies to trash", self
        )
        action_send2trash.setCheckable(True)
        action_send2trash.setChecked(True)
        action_send2trash.triggered.connect(self._file_modify.enable_send2trash)
        self._file_menu.addAction(action_send2trash)

        # menu - view
        self._view_menu = self._menu.addMenu("View")
        action_resize: QtGui.QAction = QtGui.QAction("Enable window resizing", self)
        action_resize.setCheckable(True)
        action_resize.setChecked(False)
        action_resize.triggered.connect(self.enable_resize)
        self._view_menu.addAction(action_resize)

    @QtCore.Slot()
    def exit_app(self, is_checked: bool) -> None:
        QtWidgets.QApplication.quit()

    @QtCore.Slot()
    def enable_resize(self, is_checked: bool) -> None:
        if is_checked:
            max_widget_size: int = (1 << 24) - 1
            self.setMaximumSize(max_widget_size, max_widget_size)
        else:
            self.resize(*self._SIZE)
            self.setFixedSize(*self._SIZE)

    @QtCore.Slot()
    def on_folder(self, path: str) -> None:
        self._file_list.load_directory(path)

    @QtCore.Slot()
    def on_images(self) -> None:
        paths: List[str] = self._file_list.selected_paths()
        self._image_viewer.set_images(paths)
        self._file_modify.set_images(paths)

    @QtCore.Slot()
    def on_image(self, file: Optional[Image]) -> None:
        self._file_edit.set_file(file)

    @QtCore.Slot()
    def on_modify(self, is_done: bool) -> None:
        if not is_done:
            self._file_tree.setEnabled(False)
            self._file_list.setEnabled(False)
            self._file_edit.setEnabled(False)
        else:
            self._file_tree.setEnabled(True)
            self._file_edit.setEnabled(True)
            self._file_list.setEnabled(True)

            filepaths: List[str] = self._file_modify.new_filepaths()
            self._file_list.reload(selected_filepaths=filepaths)
