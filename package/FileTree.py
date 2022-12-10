from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem
from typing import Optional
import os


class FileTree(QTreeWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)

        self.load_tree()
        self.itemSelectionChanged.connect(self.on_selection)
        self.itemExpanded.connect(self.on_expand)

    def load_tree(self) -> None:
        for i in range(65, 91):
            path: str = f"{chr(i)}:"
            if os.path.exists(f"{path}/"):
                item: QTreeWidgetItem = QTreeWidgetItem(self, [path])
                self.load_subtree(item)

    def load_subtree(self, item: QTreeWidgetItem) -> None:
        path: str = self.get_path(item)
        try:
            for dir in os.listdir(f"{path}/"):
                subpath: str = f"{path}/{dir}"
                if os.path.isdir(subpath):
                    QTreeWidgetItem(item, [os.path.basename(dir)])
        except PermissionError:
            pass

    def on_selection(self):
        item: QTreeWidgetItem = self.currentItem()
        if not item.isExpanded():
            item.setExpanded(True)

        path: str = self.get_path(item)
        print(path)

    def on_expand(self, item: QTreeWidgetItem) -> None:
        for i in range(item.childCount()):
            child: QTreeWidgetItem = item.child(i)
            self.load_subtree(child)

    def get_path(self, item: QTreeWidgetItem) -> str:
        text: str = item.text(0)
        parent: Optional[QTreeWidgetItem] = item.parent()
        if parent is not None:
            super_text: str = self.get_path(parent)
            text = "{}/{}".format(super_text, text)
        return text

    def get_depth(self, item: QTreeWidgetItem) -> int:
        depth: int = 0
        parent: Optional[QTreeWidgetItem] = item.parent()
        if parent is not None:
            depth = self.get_depth(parent) + 1
        return depth

    def get_current_path(self) -> str:
        return self.get_path(self.currentItem())
