import os
from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets, QtCore


class FileTree(QtWidgets.QWidget):
    _tree: QtWidgets.QTreeWidget
    signal_path_changed = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._tree = QtWidgets.QTreeWidget()
        layout.addWidget(self._tree)

        self._tree.setAlternatingRowColors(True)
        self._tree.setHeaderHidden(True)
        self._tree.itemSelectionChanged.connect(self.on_selection)
        self._tree.itemExpanded.connect(self.on_expand)
        self.load_tree()

    def load_tree(self) -> None:
        for i in range(65, 91):
            path: str = f"{chr(i)}:"
            if os.path.exists(f"{path}/"):
                item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                    self._tree, [path]
                )
                self.load_subtree(item)

    def load_subtree(self, item: QtWidgets.QTreeWidgetItem) -> None:
        path: str = self.item_path(item)
        try:
            with os.scandir(f"{path}/") as entries:
                for entry in entries:
                    if entry.is_dir():
                        QtWidgets.QTreeWidgetItem(item, [os.path.basename(entry)])

                # subpath: str = f"{path}/{dir}"
                # if os.path.isdir(subpath):
                #     QtWidgets.QTreeWidgetItem(item, [os.path.basename(dir)])
        except PermissionError:
            pass

    def on_selection(self):
        item: QtWidgets.QTreeWidgetItem = self._tree.currentItem()
        if not item.isExpanded():
            item.setExpanded(True)

        path: str = self.item_path(item)
        print(path)
        self.signal_path_changed.emit(path)

    def on_expand(self, item: QtWidgets.QTreeWidgetItem) -> None:
        for i in range(item.childCount()):
            child: QtWidgets.QTreeWidgetItem = item.child(i)
            self.load_subtree(child)

    def item_path(self, item: QtWidgets.QTreeWidgetItem) -> str:
        text: str = item.text(0)
        parent: Optional[QtWidgets.QTreeWidgetItem] = item.parent()
        if parent is not None:
            super_text: str = self.item_path(parent)
            text = "{}/{}".format(super_text, text)
        return text

    def depth(self, item: QtWidgets.QTreeWidgetItem) -> int:
        depth: int = 0
        parent: Optional[QtWidgets.QTreeWidgetItem] = item.parent()
        if parent is not None:
            depth = self.depth(parent) + 1
        return depth

    def selected_path(self) -> str:
        return self.item_path(self.currentItem())
