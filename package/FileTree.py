import os
import time
from typing import List, Optional

from PySide6 import QtWidgets, QtCore


class FileTree(QtWidgets.QWidget):

    _SETTING: str = "path"
    _settings: QtCore.QSettings
    _tree: QtWidgets.QTreeWidget

    signal_path_changed = QtCore.Signal(str)

    def __init__(
        self, settings: QtCore.QSettings, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings

        # layout
        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # tree
        self._tree = QtWidgets.QTreeWidget()
        self._tree.setAlternatingRowColors(True)
        self._tree.setHeaderHidden(True)
        self._tree.itemExpanded.connect(self.on_expand)
        self._tree.itemSelectionChanged.connect(self.on_selection)

        # add drives
        for i in range(65, 91):
            drive: str = f"{chr(i)}:"
            if os.path.exists(f"{drive}\\"):
                item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                    self._tree, [drive]
                )
                self.load_item(item)

        layout.addWidget(self._tree)

    def load_settings(self) -> None:
        if self._settings.contains(self._SETTING):
            path: Optional[str] = self._settings.value(self._SETTING)
            if path is not None and os.path.exists(path):
                self.load_path(path)

    def load_path(self, path: str) -> None:
        assert os.path.exists(path)
        components: List[str] = path.split("\\")

        current_item: QtWidgets.QTreeWidgetItem = self._tree.invisibleRootItem()
        for component in components:
            child_items = [
                current_item.child(i) for i in range(current_item.childCount())
            ]
            matching_items = [item for item in child_items if item.text(0) == component]

            if not matching_items:
                return None
            current_item = matching_items[0]
            current_item.setExpanded(True)
        # current_item.setSelected(True)

    @classmethod
    def load_item(cls, item: QtWidgets.QTreeWidgetItem) -> None:
        path: str = f"{cls.item_path(item)}\\"
        try:
            subfolders: List[str] = next(os.walk(path))[1]
            for subfolder in subfolders:
                QtWidgets.QTreeWidgetItem(item, [os.path.basename(subfolder)])
        except StopIteration:
            pass

        # try:
        #     with os.scandir(f"{path}") as entries:
        #         for entry in entries:
        #             if entry.is_dir():
        #                 QtWidgets.QTreeWidgetItem(item, [os.path.basename(entry)])
        # except PermissionError:
        #     pass

    @classmethod
    def item_path(cls, item: QtWidgets.QTreeWidgetItem) -> str:
        text: str = item.text(0)
        parent: Optional[QtWidgets.QTreeWidgetItem] = item.parent()
        if parent is not None:
            super_text: str = cls.item_path(parent)
            text = f"{super_text}\\{text}"
        return text

    @classmethod
    def depth(cls, item: QtWidgets.QTreeWidgetItem) -> int:
        depth: int = 0
        parent: Optional[QtWidgets.QTreeWidgetItem] = item.parent()
        if parent is not None:
            depth = cls.depth(parent) + 1
        return depth

    def selected_path(self) -> str:
        return self.item_path(self._tree.currentItem())

    # handlers
    def on_selection(self):
        item: QtWidgets.QTreeWidgetItem = self._tree.selectedItems()[0]
        if not item.isExpanded():
            item.setExpanded(True)

        path: str = self.item_path(item)
        self._settings.setValue("path", path)
        self.signal_path_changed.emit(path)

    def on_expand(self, item: QtWidgets.QTreeWidgetItem) -> None:
        t0: int = time.time()
        path: str = self.item_path(item)
        for i in range(item.childCount()):
            child: QtWidgets.QTreeWidgetItem = item.child(i)
            self.load_item(child)
        print(f"{path} [{time.time() - t0:.6f} s]")
