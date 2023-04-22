from typing import Optional, List
from PySide6 import QtWidgets, QtCore

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer
from package.FileEdit import FileEdit
from package.Image import Image
from package.FileModify import FileModify


class ExifEdit(QtWidgets.QWidget):

    _file_tree: FileTree
    _file_list: FileList
    _image_viewer: ImageViewer
    _file_edit: FileEdit
    _file_modify: FileModify

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        settings: QtCore.QSettings = QtCore.QSettings("ArtvL", "ExifEdit")

        layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # file tree
        self._file_tree: FileTree = FileTree(settings, parent=self)
        layout.addWidget(self._file_tree)

        # file list
        self._file_list: FileList = FileList(parent=self)
        layout.addWidget(self._file_list)
        self._file_tree.signal_path_changed.connect(
            self.on_folder
        )  # dependency: _file_list
        self._file_tree.load_settings()

        action_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.addItem(action_layout)

        # image viewer
        self._image_viewer: ImageViewer = ImageViewer(parent=self)
        action_layout.addWidget(self._image_viewer)
        self._file_list.signal_selection_changed.connect(
            self.on_images
        )  # dependency: self._image_viewer
        self._image_viewer.signal_image_changed.connect(
            self.on_image
        )  # dependency: self._file_edit

        frame: QtWidgets.QFrame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.HLine)
        frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        action_layout.addWidget(frame)

        # file edit
        self._file_edit: FileEdit = FileEdit(settings, parent=self)
        action_layout.addWidget(self._file_edit)
        action_layout.addStretch()

        # file modify
        self._file_modify: FileModify = FileModify(self._file_edit, parent=self)
        self._file_modify.signal_done.connect(self.on_modify)
        action_layout.addWidget(self._file_modify)

    def on_folder(self, path: str) -> None:
        self._file_list.load_directory(path)

    def on_images(self) -> None:
        paths: List[str] = self._file_list.selected_paths()
        self._image_viewer.set_images(paths)
        self._file_modify.set_images(paths)

    def on_image(self, file: Optional[Image]) -> None:
        self._file_edit.set_file(file)

    def on_modify(self, is_done: bool) -> None:
        if not is_done:
            self._file_tree.setEnabled(False)
            self._file_list.setEnabled(False)
            self._file_edit.setEnabled(False)
        else:
            self._file_tree.setEnabled(True)
            self._file_list.setEnabled(True)
            self._file_edit.setEnabled(True)
            filepaths: List[str] = self._file_modify.new_filepaths()
            self._file_list.reload(selected_filepaths=filepaths)
