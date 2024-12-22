import os
from typing import List, Optional

from PySide6 import QtWidgets, QtCore


class FileList(QtWidgets.QWidget):
    _dirpath: Optional[str]
    _filepaths: List[str]
    _index_highlight: int
    _selected: List[bool]
    _file_tree: QtWidgets.QTreeWidget
    _button_select: QtWidgets.QPushButton
    _button_deselect: QtWidgets.QPushButton
    _checkbox_select_all: QtWidgets.QCheckBox
    _selection_info: QtWidgets.QLabel

    signal_load_directory: QtCore.Signal = QtCore.Signal(int)
    signal_selection_changed: QtCore.Signal = QtCore.Signal()
    signal_highlight_changed: QtCore.Signal = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._dirpath = None
        self._filepaths = []
        self._index_highlight = 0
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

    def clear(self) -> None:
        # Clear file-tree, resets UI elements, reset all related attributes.

        self._dirpath = None
        self._filepaths = []
        self._index_highlight = 0
        self._selected = []
        self._file_tree.clear()
        self._button_select.setEnabled(False)
        self._button_deselect.setEnabled(False)
        self.update_ui()

    def update_ui(self) -> None:
        # Update the UI (file-tree dynamic UI elements: 'Select all', and the 'x/n selected'
        # selection counter).

        num_items: int = self.num_items()
        num_selected: int = self.num_selected()
        
        # update checkbox 'Select all'
        self._checkbox_select_all.blockSignals(True)
        self._checkbox_select_all.setEnabled(False)
        self._checkbox_select_all.setCheckState(QtCore.Qt.Unchecked)
        if num_items > 0:
            self._checkbox_select_all.setEnabled(True)
            if num_selected == num_items:
                self._checkbox_select_all.setCheckState(QtCore.Qt.Checked)

        # update 'x/n selected' selection counter
        self._selection_info.setText(f'{num_selected}/{num_items} selected')

        self._checkbox_select_all.blockSignals(False)

    def load_directory(
        self,
        dirpath: str,
        selected_filepaths: Optional[List[str]] = None,
        highlighted_filepaths: Optional[List[str]] = None,
    ) -> None:
        # Loads a directory: lists all files that end with '.jpg' or .jpeg' (case insensitive)
        # within the directory. Optionally, files to be highlighted and selected can be provided
        # as arguments.

        assert os.path.exists(dirpath), f"'{dirpath}' does not exist!"

        # clear state
        self.clear()
        self._dirpath = dirpath

        # add items to file-tree
        self._file_tree.blockSignals(True)
        try:
            filenames: List[str] = os.listdir(dirpath)
            filenames.sort()
            for filename in filenames:
                filepath: str = os.path.join(dirpath, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(
                    (".jpg", ".jpeg")
                ):
                    self._filepaths.append(filepath)

                    # create file-tree items
                    item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                        self._file_tree, [filename]
                    )

                    # configure item selection
                    is_selected: bool = False
                    if selected_filepaths is not None:
                        is_selected: bool = filepath in selected_filepaths
                    self._selected.append(is_selected)
                    checkstate: QtCore.Qt.CheckState = (
                        QtCore.Qt.Checked if is_selected else QtCore.Qt.Unchecked
                    )
                    item.setCheckState(0, checkstate)

                    # configure item highlighting
                    is_highlighted: bool = False
                    if highlighted_filepaths is not None:
                        is_highlighted = filepath in highlighted_filepaths
                    item.setSelected(is_highlighted)
            
            # update 'Select all' and 'Deselect all' buttons
            if self.num_items() > 0:
                first_item: QtWidgets.QTreeWidgetItem = self._file_tree.topLevelItem(0)
                self._file_tree.setCurrentItem(first_item)
                self._button_select.setEnabled(True)
                self._button_deselect.setEnabled(True)
            self.update_ui()

        except PermissionError:
            pass

        self._file_tree.blockSignals(False)
        self.signal_load_directory.emit(self.num_items())

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

    def increment_highlight(self, increment: int = 1) -> Optional[str]:
        # Changes the highlighted item as an (positive or negative) incremenet from the first
        # highlighted item. Function returns the path of the new highlighted item if the tree
        # contains items; otherwise it will return None.

        num_paths: int = self.num_items()
        if num_paths > 0:
            new_index: int = (self._index_highlight + increment) % num_paths
            self._index_highlight = new_index
            item: QtWidgets.QTreeWidgetItem = self._file_tree.topLevelItem(new_index)
            self._file_tree.setCurrentItem(item)
            return self.path_from_index(new_index)
        return None

    def next_highlight(self) -> str:
        # Returns the path of the next highlighted item (increment +1).

        return self.increment_highlight(1)

    def previous_highlight(self) -> str:
        # Returns the path of the previous highlighted item (increment -1).

        return self.increment_highlight(-1)

    def item_with_path(self, path: str) -> Optional[QtWidgets.QTreeWidgetItem]:
        if path in self._filepaths:
            index: int = self._filepaths.index(path)
            return self._file_tree.topLevelItem(index)
        return None

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

    def path_from_index(self, index: int) -> str:
        # Returns the file-path of the item at a given index.
        
        assert index < self.num_items()
        return self._filepaths[index]

    def paths(self) -> List[str]:
        # Returns all file-paths.

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
        # Updates buttons 'Select highlighted' and 'Deselect highlighted', and emits signal
        # 'signal_highlight_changed' after a highlight change was made.

        # update 'Select highlighted' and 'Deselect highlighted' buttons
        if self.num_highlighted() > 0:
            self._button_select.setEnabled(True)
            self._button_deselect.setEnabled(True)

            # find first highlighted item
            first_item: QtWidgets.QTreeWidgetItem = self._file_tree.selectedItems()[0]
            first_item_index: int = self._file_tree.indexOfTopLevelItem(first_item)

            # if first highlighted item changed
            if first_item_index != self._index_highlight:
                self._index_highlight = first_item_index
                path: str = self.path_from_index(first_item_index)
                self.signal_highlight_changed.emit(path)

        else:
            self._button_select.setEnabled(False)
            self._button_deselect.setEnabled(False)

    def on_check_select(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        # Updates 'self._selected' and UI after an item selection was changed via its checkbox.

        is_selected: bool = item.checkState(column) == QtCore.Qt.Checked
        index: int = self._file_tree.indexOfTopLevelItem(item)
        self._selected[index] = is_selected
        
        self.update_ui()
        self.signal_selection_changed.emit()

    def on_select_highlight(self, is_selected: bool) -> None:
        # Updates the checkboxes of highlighted items, 'self._selected' and UI, after the 'Select
        # highlighted' or 'Deselect highlighted' buttons were pressed.

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
        self.signal_selection_changed.emit()

    def on_select_all(self, is_selected: bool) -> None:
        # Updates the checkboxes of all items, 'self._selected' and UI after the 'Select all'
        # button was pressed.

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
        self.signal_selection_changed.emit()
