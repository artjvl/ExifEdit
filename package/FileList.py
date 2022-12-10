from PIL import Image, ExifTags
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaMetaData
from typing import Optional
import os
from typing import List


class FileList(QTreeWidget):
    _path_list: List[str]
    _checked_list: List[bool]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.itemChanged.connect(self.handle_checked)
        self._path_list = []
        self._checked_list = []

    def load_directory(self, path: str) -> None:
        assert os.path.exists(path)
        self.clear()
        self._path_list = []
        self._checked_list = []

        self.blockSignals(True)
        try:
            for filename in os.listdir(path):
                filepath: str = f"{path}/{filename}"
                if os.path.isfile(filepath) and filename.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    self._path_list.append(filepath)
                    self._checked_list.append(False)
                    item: QTreeWidgetItem = QTreeWidgetItem(self, [filename])
                    item.setCheckState(0, Qt.Unchecked)
        except PermissionError:
            pass
        self.blockSignals(False)

    def populate_tree(self):
        pass

    def handle_checked(self, item: QTreeWidgetItem, column: int) -> None:
        checked: bool = item.checkState(column) == Qt.Checked
        index: int = self.indexFromItem(item).row()
        self._checked_list[index] = checked
        print(f"{index}-{checked}: {self._path_list[index]}")

    def select_all(self, is_checked: bool) -> None:
        for i, _ in enumerate(self._checked_list):
            self._checked_list[i] = is_checked

    def selected_paths(self) -> List[str]:
        paths: List[str]
        for i, path in enumerate(self._path_list):
            if self._checked_list[i]:
                paths.append(path)
        return paths
