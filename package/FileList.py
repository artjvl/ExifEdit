import os
from typing import List, Optional

from PySide6 import QtWidgets, QtCore


class FileList(QtWidgets.QWidget):
    _path_list: List[str]
    _selected_list: List[bool]
    _file_tree: QtWidgets.QTreeWidget
    _button_select: QtWidgets.QPushButton
    _button_deselect: QtWidgets.QPushButton
    _checkbox_select_all: QtWidgets.QCheckBox
    _selection_info: QtWidgets.QLabel

    signal_selection_changed: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._path_list = []
        self._selected_list = []
        self._file_tree = QtWidgets.QTreeWidget(parent=self)
        self._file_tree.setAlternatingRowColors(True)
        self._file_tree.setHeaderHidden(True)
        self._file_tree.itemChanged.connect(self.on_check_select)
        self._file_tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._file_tree.selectionModel().selectionChanged.connect(self.on_highlight)
        self._button_select: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Select highlighted", parent=self
        )
        self._button_select.setEnabled(False)
        self._button_select.pressed.connect(lambda: self.on_select_highlight(True))
        self._button_deselect: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Deselect highlighted", parent=self
        )
        self._button_deselect.setEnabled(False)
        self._button_deselect.pressed.connect(lambda: self.on_select_highlight(False))
        self._checkbox_select_all: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Select all", parent=self
        )
        self._checkbox_select_all.setEnabled(False)
        self._checkbox_select_all.toggled.connect(self.on_select_all)
        self._selection_info: QtWidgets.QLabel = QtWidgets.QLabel(parent=self)

        button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self._button_select)
        button_layout.addWidget(self._button_deselect)

        selection_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        selection_layout.setContentsMargins(0, 0, 0, 0)
        selection_layout.addWidget(self._checkbox_select_all)
        selection_layout.addWidget(self._selection_info, 0, QtCore.Qt.AlignRight)

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
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
                filepath: str = f"{path}\\{filename}"
                if os.path.isfile(filepath) and filename.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    self._path_list.append(filepath)
                    self._selected_list.append(False)
                    item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                        self._file_tree, [filename]
                    )
                    item.setCheckState(0, QtCore.Qt.Unchecked)
        except PermissionError:
            pass
        self._file_tree.blockSignals(False)
        self.update_info()

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
        has_items: bool = self.get_num_items() > 0
        self._checkbox_select_all.setEnabled(has_items)

        num_selected: int = self.get_num_selected()
        if num_selected == 0:
            self._checkbox_select_all.setCheckState(QtCore.Qt.Unchecked)
        elif num_selected == self.get_num_items():
            self._checkbox_select_all.setCheckState(QtCore.Qt.Checked)
        self._selection_info.setText(
            f"{self.get_num_selected()}\\{self.get_num_items()} selected"
        )

        self.signal_selection_changed.emit()

    def on_highlight(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        if self.get_num_highlighted() > 0:
            self._button_select.setEnabled(True)
            self._button_deselect.setEnabled(True)
        else:
            self._button_select.setEnabled(False)
            self._button_deselect.setEnabled(False)
        # for index in selected.indexes():
        #     item: QtWidgets.QTreeWidgetItem = self._file_tree.itemFromIndex(index)
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

    def on_check_select(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        is_selected: bool = item.checkState(column) == QtCore.Qt.Checked
        index: int = self._file_tree.indexOfTopLevelItem(item)
        self._selected_list[index] = is_selected
        self.update_info()

    def on_select_highlight(self, is_selected: bool) -> None:
        checkstate: QtCore.Qt.CheckState = (
            QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
        )

        self._file_tree.blockSignals(True)
        for item in self._file_tree.selectedItems():
            i: int = self._file_tree.indexOfTopLevelItem(item)
            self._selected_list[i] = is_selected
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)

        self.update_info()

    def on_select_all(self, is_selected: bool) -> None:
        checkstate: QtCore.Qt.CheckState = (
            QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
        )

        self._file_tree.blockSignals(True)
        for i, _ in enumerate(self._selected_list):
            self._selected_list[i] = is_selected
            item: QtWidgets.QTreeWidgetItem = self._file_tree.topLevelItem(i)
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)

        self.update_info()

    def selected_paths(self) -> List[str]:
        return [
            path for i, path in enumerate(self._path_list) if self._selected_list[i]
        ]
