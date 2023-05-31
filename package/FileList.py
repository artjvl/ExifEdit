import os
from typing import List, Optional

from PySide6 import QtWidgets, QtCore


class FileList(QtWidgets.QWidget):
    _dirpath: Optional[str]
    _filepaths: List[str]
    _selected: List[bool]
    _file_tree: QtWidgets.QTreeWidget
    _button_select: QtWidgets.QPushButton
    _button_deselect: QtWidgets.QPushButton
    _checkbox_select_all: QtWidgets.QCheckBox
    _selection_info: QtWidgets.QLabel

    signal_selection_changed: QtCore.Signal = QtCore.Signal()
    signal_highlight_changed: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._dirpath = None
        self._filepaths = []
        self._selected = []
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

    def load_directory(
        self,
        dirpath: str,
        selected_filepaths: Optional[List[str]] = None,
        highlighted_filepaths: Optional[List[str]] = None,
    ) -> None:
        assert os.path.exists(dirpath)

        # clear state
        self.clear()
        self._dirpath = dirpath

        # add items to file-tree
        self._file_tree.blockSignals(True)

        try:
            filenames: List[str] = os.listdir(dirpath)
            filenames.sort()
            for filename in filenames:
                filepath: str = f"{dirpath}\\{filename}"
                if os.path.isfile(filepath) and filename.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    self._filepaths.append(filepath)
                    item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                        self._file_tree, [filename]
                    )

                    # selection
                    is_selected: bool = False
                    if selected_filepaths is not None:
                        is_selected: bool = filepath in selected_filepaths
                    self._selected.append(is_selected)
                    checkstate: QtCore.Qt.CheckState = (
                        QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
                    )
                    item.setCheckState(0, checkstate)

                    # highlight
                    is_highlighted: bool = False
                    if highlighted_filepaths is not None:
                        is_highlighted = filepath in highlighted_filepaths
                    item.setSelected(is_highlighted)

        except PermissionError:
            pass

        self._file_tree.blockSignals(False)

        # update UI
        self.update_ui()

    def reload(
        self,
        selected_filepaths: Optional[List[str]] = None,
        highlighted_filepaths: Optional[List[str]] = None,
    ) -> None:
        return self.load_directory(
            self._dirpath,
            selected_filepaths=selected_filepaths,
            highlighted_filepaths=highlighted_filepaths,
        )

    def clear(self) -> None:
        self._dirpath = None
        self._filepaths = []
        self._selected = []
        self._file_tree.clear()

    def update_ui(self) -> None:
        has_items: bool = self.num_items() > 0
        self._checkbox_select_all.setEnabled(has_items)

        num_selected: int = self.num_selected()
        if num_selected == 0:
            self._checkbox_select_all.setCheckState(QtCore.Qt.Unchecked)
        elif num_selected == self.num_items():
            self._checkbox_select_all.setCheckState(QtCore.Qt.Checked)
        self._selection_info.setText(
            f"{self.num_selected()}\\{self.num_items()} selected"
        )

        self.signal_selection_changed.emit()

    def item_with_text(self, text: str) -> Optional[QtWidgets.QTreeWidgetItem]:
        for i in range(self._file_tree.topLevelItemCount()):
            item = self._file_tree.topLevelItem(i)
            if item.text(0) == text:
                return item
        return None

    def select_item_with_text(self, text: str) -> None:
        item: Optional[QtWidgets.QTreeWidgetItem] = self.item_with_text(text)
        if item is not None:
            self._file_tree.setCurrentItem(item)

    def paths(self) -> List[str]:
        return self._filepaths

    def selected_paths(self) -> List[str]:
        return [path for i, path in enumerate(self._filepaths) if self._selected[i]]

    def highlighted_paths(self) -> List[str]:
        return [
            self._filepaths[self._file_tree.indexOfTopLevelItem(item)]
            for item in self._file_tree.selectedItems()
        ]

    def num_items(self) -> int:
        return len(self._filepaths)

    def num_highlighted(self) -> int:
        return len(self._file_tree.selectedItems())

    def num_selected(self) -> int:
        return sum(self._selected)

    # handlers
    def on_highlight(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        if self.num_highlighted() > 0:
            self._button_select.setEnabled(True)
            self._button_deselect.setEnabled(True)
        else:
            self._button_select.setEnabled(False)
            self._button_deselect.setEnabled(False)
        self.signal_highlight_changed.emit()

    def on_check_select(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        is_selected: bool = item.checkState(column) == QtCore.Qt.Checked
        index: int = self._file_tree.indexOfTopLevelItem(item)
        self._selected[index] = is_selected
        self.update_ui()

    def on_select_highlight(self, is_selected: bool) -> None:
        checkstate: QtCore.Qt.CheckState = (
            QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
        )

        self._file_tree.blockSignals(True)
        for item in self._file_tree.selectedItems():
            index: int = self._file_tree.indexOfTopLevelItem(item)
            self._selected[index] = is_selected
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)

        self.update_ui()

    def on_select_all(self, is_selected: bool) -> None:
        checkstate: QtCore.Qt.CheckState = (
            QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
        )

        self._file_tree.blockSignals(True)
        for i, _ in enumerate(self._selected):
            self._selected[i] = is_selected
            item: QtWidgets.QTreeWidgetItem = self._file_tree.topLevelItem(i)
            item.setCheckState(0, checkstate)
        self._file_tree.blockSignals(False)

        self.update_ui()
