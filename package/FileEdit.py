from __future__ import annotations
import re
import datetime
from typing import List, Optional

from PySide6 import QtCore, QtWidgets, QtGui

from package.ChangeDateTaken import ChangeDateTaken
from package.ChangeFileName import ChangeFileName
from package.ExifFile import ExifFile, ExifField
from package.NestedList import NestedListItem


class FileEdit(QtWidgets.QWidget):

    _file: Optional[ExifFile]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._file = None

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        self._change_filename = ChangeFileName()
        self._change_filename.signal_changed.connect(self.on_filename_changed)
        layout.addWidget(self._change_filename)

        self._change_date_taken = ChangeDateTaken()
        self._change_date_taken.signal_changed.connect(self.on_date_taken_changed)
        layout.addWidget(self._change_date_taken)

        self._preview_tree = self.create_preview_tree()
        self._preview_box: QtWidgets.QGroupBox = QtWidgets.QGroupBox("Preview")
        preview_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        preview_layout.setContentsMargins(6, 6, 6, 6)
        preview_layout.addWidget(self._preview_tree)
        self._preview_box.setLayout(preview_layout)
        layout.addWidget(self._preview_box)

    def set_file(self, file: Optional[ExifFile]):
        self._file = file
        if file is not None:
            self._change_date_taken.set_file(file)
            self._change_filename.set_file(file)
        else:
            self.clear_preview()

    def create_preview_tree(self) -> QtWidgets.QTreeWidget:
        tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0%); font-size: 8pt; border-style: none;"
        )
        tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        tree.setFocusPolicy(QtCore.Qt.NoFocus)
        tree.setIndentation(0)
        tree.setColumnCount(2)
        tree.setColumnWidth(0, 90)
        # tree.setFixedHeight(160)

        empty_file = ExifFile()
        QtWidgets.QTreeWidgetItem(tree, [empty_file.filename().title(), ""])
        QtWidgets.QTreeWidgetItem(tree, [empty_file.date_taken().title(), ""])

        return tree

    def clear_preview(self) -> None:
        self.preview_filename(None)
        self.preview_date_taken(None)

    def preview_date_taken(self, date_time: Optional[datetime.datetime]) -> None:
        date_time_text: str = ""
        if date_time is not None:
            date_time_text = f"{date_time}"
        tree_item: QtWidgets.QTreeWidgetItem = self._preview_tree.topLevelItem(1)
        tree_item.setText(1, date_time_text)
        tree_item.setToolTip(1, date_time_text)

    def preview_filename(self, filename: Optional[str]) -> None:
        filename_text: str = ""
        if filename is not None:
            filename_text = filename
        tree_item: QtWidgets.QTreeWidgetItem = self._preview_tree.topLevelItem(0)
        tree_item.setText(1, filename_text)
        tree_item.setToolTip(1, filename_text)

    # handlers
    def on_date_taken_changed(self, dt: Optional[datetime.datetime]) -> None:
        self.preview_date_taken(dt)
        self._change_filename.set_date_time(dt)

    def on_filename_changed(self, name: Optional[str]) -> None:
        self.preview_filename(name)
