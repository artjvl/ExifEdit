from PIL import Image, ExifTags
from PySide6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QCheckBox,
    QPushButton,
    QLabel,
    QLayout,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6 import QtGui
from PySide6.QtCore import Qt, QItemSelection
from typing import Optional
import os
from typing import List


class FileList(QWidget):
    _path_list: List[str]
    _selected_list: List[bool]
    _file_tree: QTreeWidget
    _button_select: QPushButton
    _button_deselect: QPushButton
    _checkbox_select_all: QCheckBox
    _selection_info: QLabel

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._path_list = []
        self._selected_list = []
        self._file_tree = QTreeWidget()
        self._file_tree.setAlternatingRowColors(True)
        self._file_tree.setHeaderHidden(True)
        self._file_tree.itemChanged.connect(self.handle_selection)
        self._file_tree.selectionModel().selectionChanged.connect(self.handle_highlight)
        self._file_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._button_select: QPushButton = QPushButton("Select highlighted")
        self._button_select.setEnabled(False)
        self._button_select.pressed.connect(lambda: self.handle_select_highlight(True))
        self._button_deselect: QPushButton = QPushButton("Deselect highlighted")
        self._button_deselect.setEnabled(False)
        self._button_deselect.pressed.connect(
            lambda: self.handle_select_highlight(False)
        )
        self._checkbox_select_all: QCheckBox = QCheckBox("Select all")
        self._checkbox_select_all.setEnabled(False)
        self._checkbox_select_all.toggled.connect(self.select_all)
        self._selection_info: QLabel = QLabel()

        button_layout: QLayout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self._button_select)
        button_layout.addWidget(self._button_deselect)

        selection_layout: QLayout = QHBoxLayout()
        selection_layout.setContentsMargins(0, 0, 0, 0)
        selection_layout.addWidget(self._checkbox_select_all)
        selection_layout.addWidget(self._selection_info, 0, Qt.AlignRight)

        layout: QLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addItem(button_layout)
        layout.addWidget(self._file_tree)
        layout.addItem(selection_layout)
        self.setLayout(layout)

    def load_directory(self, path: str) -> None:
        assert os.path.exists(path)
        self.clear()

        self._file_tree.blockSignals(True)
        try:
            for filename in os.listdir(path):
                filepath: str = f"{path}/{filename}"
                if os.path.isfile(filepath) and filename.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    self._path_list.append(filepath)
                    self._selected_list.append(False)
                    item: QTreeWidgetItem = QTreeWidgetItem(self._file_tree, [filename])
                    # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.Unchecked)
        except PermissionError:
            pass
        self._file_tree.blockSignals(False)
        self.update_info()
        self._checkbox_select_all.setEnabled(True)

    def get_num_items(self) -> int:
        return len(self._selected_list)

    def get_num_highlighted(self) -> int:
        return len(self._file_tree.selectedItems())

    def get_num_selected(self) -> int:
        return sum(self._selected_list)

    def clear(self) -> None:
        self._path_list = []
        self._selected_list = []
        self._file_tree.clear()

    def update_info(self) -> None:
        self._selection_info.setText(
            f"{self.get_num_selected()}/{self.get_num_items()} selected"
        )

    def handle_highlight(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if self.get_num_highlighted() > 0:
            self._button_select.setEnabled(True)
            self._button_deselect.setEnabled(True)
        else:
            self._button_select.setEnabled(False)
            self._button_deselect.setEnabled(False)
        # for index in selected.indexes():
        #     item: QTreeWidgetItem = self._file_tree.itemFromIndex(index)
        #     print(
        #         "SEL: row: %s, col: %s, text: %s"
        #         % (index.row(), index.column(), item.text(0))
        #     )
        # for index in deselected.indexes():
        #     item = self._file_tree.itemFromIndex(index)
        #     print(
        #         "DESEL: row: %s, col: %s, text: %s"
        #         % (index.row(), index.column(), item.text(0))
        #     )

    def handle_selection(self, item: QTreeWidgetItem, column: int) -> None:
        is_selected: bool = item.checkState(column) == Qt.Checked
        index: int = self._file_tree.indexOfTopLevelItem(item)
        self._selected_list[index] = is_selected
        self.update_info()
        # print(f"{index}-{checked}: {self._path_list[index]}")

    def handle_select_highlight(self, is_selected: bool) -> None:
        assert type(is_selected) == bool

        checkstate: Qt.CheckState = Qt.Checked if is_selected else Qt.Unchecked
        self._file_tree.blockSignals(True)
        for item in self._file_tree.selectedItems():
            i: int = self._file_tree.indexOfTopLevelItem(item)
            self._selected_list[i] = is_selected
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)
        self.update_info()

    def select_all(self, is_selected: bool) -> None:
        assert type(is_selected) == bool

        checkstate: Qt.CheckState = Qt.Checked if is_selected else Qt.Unchecked
        self._file_tree.blockSignals(True)
        for i, _ in enumerate(self._selected_list):
            self._selected_list[i] = is_selected
            item: QTreeWidgetItem = self._file_tree.topLevelItem(i)
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)
        self.update_info()

    def selected_paths(self) -> List[str]:
        paths: List[str]
        for i, path in enumerate(self._path_list):
            if self._selected_list[i]:
                paths.append(path)
        return paths
