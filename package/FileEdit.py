from __future__ import annotations
import datetime
from typing import Optional

from PySide6 import QtCore, QtWidgets

from package.ChangeDateTaken import ChangeDateTaken
from package.ChangeFileName import ChangeFileName
from package.ExifFile import ExifFile


class FileEdit(QtWidgets.QWidget):

    _file: Optional[ExifFile]
    _dt: Optional[datetime.datetime]
    _filename: Optional[str]
    _is_checked: bool

    signal_checked = QtCore.Signal(bool)

    def __init__(
        self, settings: QtCore.QSettings, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._file = None
        self._dt = None
        self._filename = None
        self._is_checked = False

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self._change_date_taken = ChangeDateTaken(settings)
        self._change_date_taken.signal_changed.connect(self.on_date_taken_changed)
        self._change_filename = ChangeFileName(self._change_date_taken, settings)
        self._change_filename.signal_changed.connect(self.on_filename_changed)
        layout.addWidget(self._change_filename)
        layout.addWidget(self._change_date_taken)

        preview_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self._preview_box: QtWidgets.QGroupBox = QtWidgets.QGroupBox("Preview")
        layout.addWidget(self._preview_box)
        self._preview_box.setLayout(preview_layout)
        preview_layout.setContentsMargins(6, 6, 6, 6)
        self._preview_tree = self.create_preview_tree()
        preview_layout.addWidget(self._preview_tree)

    def is_checked(self) -> bool:
        return (
            self._change_filename.is_checked() or self._change_date_taken.is_checked()
        )

    def set_file(self, file: Optional[ExifFile]) -> None:
        self._file = file

        dt: Optional[datetime.datetime] = None
        if file is not None:
            dt: Optional[datetime.datetime] = file.date_taken().value()

        self._change_date_taken.set_date_taken(dt)
        self._change_filename.set_file(file)

    def convert_file(self, file: ExifFile) -> Optional[str]:
        new_filename: Optional[str] = self._change_filename.convert_filename(file)

        dt: Optional[datetime.datetime] = file.date_taken().value()
        new_dt: Optional[
            datetime.datetime
        ] = self._change_date_taken.convert_date_taken(dt)

        if new_dt is None:
            if new_filename is None:
                return None
        else:
            file.set_date_taken(new_dt)
            if new_filename is None:
                new_filename = file.get_filename()

        return new_filename

    # preview
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
        tree.setColumnWidth(0, 70)
        # tree.setFixedHeight(160)

        empty_file = ExifFile()
        QtWidgets.QTreeWidgetItem(tree, [empty_file.filename().description(), ""])
        QtWidgets.QTreeWidgetItem(tree, [empty_file.date_taken().description(), ""])

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

    # emit
    def emit_checked(self) -> None:
        is_checked: bool = self.is_checked()
        if is_checked is not self._is_checked:
            self._is_checked = is_checked
            self.signal_checked.emit(is_checked)

    # handlers
    def on_date_taken_changed(self, dt: Optional[datetime.datetime]) -> None:
        self._dt = dt
        self.preview_date_taken(dt)
        self.emit_checked()

    def on_filename_changed(self, filename: Optional[str]) -> None:
        self._filename = filename
        self.preview_filename(filename)
        self.emit_checked()
