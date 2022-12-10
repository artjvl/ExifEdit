from PySide6.QtWidgets import QWidget, QLayout, QHBoxLayout
from typing import Optional
import os

from package.FileList import FileList
from package.FileTree import FileTree


class FileExplorer(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._file_tree: FileTree = FileTree()
        self._file_list: FileList = FileList()
        self._file_tree.itemSelectionChanged.connect(self.on_selection)

        layout: QLayout = QHBoxLayout()
        layout.addWidget(self._file_tree)
        layout.addWidget(self._file_list)
        self.setLayout(layout)

    def on_selection(self) -> None:
        path: str = self._file_tree.get_current_path()
        self._file_list.load_directory(path)
