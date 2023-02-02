from PySide6.QtWidgets import QWidget, QLayout, QHBoxLayout
from typing import Optional, List
import os

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer


class ExifEdit(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._file_tree: FileTree = FileTree(parent=self)
        self._file_list: FileList = FileList(parent=self)
        self._file_tree.itemSelectionChanged.connect(self.on_folder)
        self._image_viewer: ImageViewer = ImageViewer(parent=self)
        self._file_list.signal_selection_changed.connect(self.on_images)

        layout: QLayout = QHBoxLayout()
        layout.addWidget(self._file_tree)
        layout.addWidget(self._file_list)
        layout.addWidget(self._image_viewer)
        self.setLayout(layout)

    def on_folder(self) -> None:
        path: str = self._file_tree.selected_path()
        self._file_list.load_directory(path)

    def on_images(self) -> None:
        paths: List[str] = self._file_list.selected_paths()
        self._image_viewer.load_images(paths)
