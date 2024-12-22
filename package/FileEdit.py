from __future__ import annotations
import datetime
from typing import Optional

from PySide6 import QtCore, QtWidgets

from package.ChangeDateTaken import ChangeDateTaken
from package.ChangeFileName import ChangeFileName
from package.Image import Image


class FileEdit(QtWidgets.QWidget):

    _file: Optional[Image]
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

        # preview tree
        self._preview_tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        self._preview_tree.setHeaderHidden(True)
        self._preview_tree.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0%); font-size: 10pt; border-style: none;"
        )
        self._preview_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._preview_tree.setFocusPolicy(QtCore.Qt.NoFocus)
        self._preview_tree.setIndentation(0)
        self._preview_tree.setColumnCount(2)
        self._preview_tree.setColumnWidth(0, 70)
        QtWidgets.QTreeWidgetItem(self._preview_tree, ["File name", ""])
        QtWidgets.QTreeWidgetItem(self._preview_tree, ["Date taken", ""])

        # preview layout
        preview_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        preview_layout.setContentsMargins(6, 6, 6, 6)
        preview_layout.addWidget(self._preview_tree)
        self._preview_box: QtWidgets.QGroupBox = QtWidgets.QGroupBox("Preview")
        self._preview_box.setLayout(preview_layout)
        layout.addWidget(self._preview_box)

    def is_checked(self) -> bool:
        return (
            self._change_filename.is_checked() or self._change_date_taken.is_checked()
        )

    def set_file(self, file: Image) -> None:
        self._file = file

        dt: Optional[datetime.datetime] = file.date_taken()

        self._change_date_taken.set_date_taken(dt)
        self._change_filename.set_file(file)

    def convert_file(self, img: Image) -> Optional[str]:
        new_filename: Optional[str] = self._change_filename.convert_filename(img)

        dt: Optional[datetime.datetime] = img.date_taken()
        new_dt: Optional[
            datetime.datetime
        ] = self._change_date_taken.convert_date_taken(dt)

        if new_dt is None:
            if new_filename is None:
                return None
        else:
            img.set_date_taken(new_dt)
            if new_filename is None:
                new_filename = img.filename()

        return new_filename

    # preview
    def clear(self) -> None:
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

        # only send out signal when is_checked changes
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
