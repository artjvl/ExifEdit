from typing import Optional, List
from PySide6 import QtWidgets, QtCore

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer
from package.FileEdit import FileEdit
from package.ExifFile import ExifFile
from package.FileModify import FileModify


class ExifEdit(QtWidgets.QWidget):
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
        action_layout.addWidget(self._file_modify)

    def on_folder(self, path: str) -> None:
        self._file_list.load_directory(path)

    def on_images(self) -> None:
        paths: List[str] = self._file_list.selected_paths()
        self._image_viewer.set_images(paths)
        self._file_modify.set_images(paths)

    def on_image(self, file: Optional[ExifFile]) -> None:
        self._file_edit.set_file(file)
