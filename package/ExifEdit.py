import os
from typing import Optional, List
from PySide6 import QtWidgets

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer
from package.FileEdit import FileEdit
from package.ExifFile import ExifFile


class ExifEdit(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self._file_tree: FileTree = FileTree(parent=self)
        self._file_list: FileList = FileList(parent=self)
        self._file_tree.signal_path_changed.connect(self.on_folder)
        self._image_viewer: ImageViewer = ImageViewer(parent=self)
        self._file_list.signal_selection_changed.connect(self.on_images)
        frame: QtWidgets.QFrame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.HLine)
        frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self._file_edit: FileEdit = FileEdit(parent=self)
        self._image_viewer.signal_image_changed.connect(self.on_image)

        layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._file_tree)
        layout.addWidget(self._file_list)
        action_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        action_layout.addWidget(self._image_viewer)
        action_layout.addWidget(frame)
        action_layout.addWidget(self._file_edit)
        action_layout.addStretch()
        layout.addItem(action_layout)
        self.setLayout(layout)

    def on_folder(self, path: str) -> None:
        self._file_list.load_directory(path)

    def on_images(self) -> None:
        paths: List[str] = self._file_list.selected_paths()
        self._image_viewer.load_images(paths)

    def on_image(self, file: ExifFile) -> None:
        self._file_edit.set_file(file)
