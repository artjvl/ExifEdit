from __future__ import annotations
import datetime
from typing import List, Optional
from PySide6 import QtWidgets, QtCore

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

    def set_file(self, file: Optional[ExifFile] = None):
        self._file = file
        self._change_date_taken.set_file_date_time(file.date_taken().value())

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

    def fill_preview(
        self,
        filename: Optional[str] = None,
        date_taken: Optional[datetime.datetime] = None,
    ):
        if filename is not None:
            self._preview_tree.topLevelItem(0).setText(1, filename)
        if date_taken is not None:
            self._preview_tree.topLevelItem(1).setText(1, f"{date_taken}")

    # handlers
    def on_date_taken_changed(self, dt: datetime.datetime) -> None:
        self.fill_preview(date_taken=dt)


class ChangeDateTaken(QtWidgets.QWidget):

    _nested: NestedListItem
    _nested_dt: NestedListItem
    _nested_dt_relative: NestedListItem
    _nested_dt_specific: NestedListItem
    _nested_name: NestedListItem
    _datetime_relative: RelativeDateTime
    _datetime_specific: SpecificDateTime
    _is_specific_changed: bool
    _date_time: Optional[datetime.datetime]

    signal_changed = QtCore.Signal(datetime.datetime)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._is_specific_changed = False
        self._date_time = None

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._nested = NestedListItem()
        layout.addWidget(self._nested)

        # Change Date taken
        self._nested_dt = self._nested.add_child(
            text="Change Date taken", is_exclusive=True
        )
        self._nested_dt.signal_checked.connect(self.on_update)

        self._datetime_relative = RelativeDateTime()
        self._datetime_relative.signal_changed.connect(self.on_relative)
        self._nested_dt_relative = self._nested_dt.add_child(
            "Relative to Date taken", self._datetime_relative
        )
        self._nested_dt_relative.signal_checked.connect(
            lambda b: self.on_relative() if b else None
        )

        self._datetime_specific = SpecificDateTime()
        self._datetime_specific.signal_changed.connect(self.on_specific_changed)
        self._nested_dt_specific = self._nested_dt.add_child(
            "Specific date/time", self._datetime_specific
        )
        self._nested_dt_specific.signal_checked.connect(
            lambda b: self.on_specific() if b else None
        )

        # Change File name
        self._nested_name = self._nested.add_child("Change File name")

    # public
    def has_file_date_time(self) -> bool:
        return self._date_time is not None

    def set_file_date_time(self, dt: datetime.datetime) -> None:
        self._date_time = dt
        if not self._is_specific_changed:
            self._datetime_specific.set_date_time(dt, is_emit=False)
        self.on_update()

    def relative(self) -> datetime.timedelta:
        return self._datetime_relative.time_delta()

    def specific(self) -> datetime.datetime:
        return self._datetime_specific.date_time()

    # handlers
    def on_update(self) -> None:
        if self._nested_dt.is_checked():
            if self._nested_dt_relative.is_checked() and self.has_file_date_time():
                self.on_relative()
            if self._nested_dt_specific.is_checked():
                self.on_specific()
        else:
            print(f"default: {self._date_time}")
            self.signal_changed.emit(self._date_time)

    def on_relative(self) -> None:
        if self.has_file_date_time():
            dt: datetime.datetime = self._datetime_relative.date_time(self._date_time)
            print(f"time-delta: {dt} ({self.relative()})")
            self.signal_changed.emit(dt)

    def on_specific(self) -> None:
        dt: datetime.datetime = self.specific()
        print(f"specific: {dt}")
        self.signal_changed.emit(dt)

    def on_specific_changed(self) -> None:
        self._is_specific_changed = True
        self.on_specific()


class RelativeDateTime(QtWidgets.QWidget):

    signal_changed = QtCore.Signal(datetime.timedelta)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # combobox +/-
        self._combobox_pm = QtWidgets.QComboBox()
        self._combobox_pm.addItems(["+", "-"])
        self._combobox_pm.setMaximumWidth(40)
        self._combobox_pm.currentIndexChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._combobox_pm)

        # spinbox day(s)
        self._spinbox_days = QtWidgets.QSpinBox()
        self._spinbox_days.setMaximumWidth(50)
        self._spinbox_days.valueChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._spinbox_days)
        label_days = QtWidgets.QLabel("day(s)")
        label_days.setMaximumWidth(40)
        layout.addWidget(label_days)

        # timeedit relative
        self._timeedit_relative = QtWidgets.QTimeEdit()
        self._timeedit_relative.setDisplayFormat("hh:mm:ss")
        self._timeedit_relative.timeChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._timeedit_relative)
        self.setLayout(layout)

    def date_time(self, dt: datetime.datetime) -> datetime.datetime:
        return dt + self.plus_minus() * self.time_delta()

    def plus_minus(self) -> int:
        current_text: str = self._combobox_pm.currentText()
        if current_text == "+":
            return 1
        return -1

    def days(self) -> int:
        return self._spinbox_days.value()

    def time_delta(self) -> datetime.timedelta:
        time: QtCore.QTime = self._timeedit_relative.time()
        return datetime.timedelta(
            days=self.days(),
            hours=time.hour(),
            minutes=time.minute(),
            seconds=time.second(),
        )


class SpecificDateTime(QtWidgets.QWidget):

    _dateedit: QtWidgets.QDateEdit
    _timeedit: QtWidgets.QTimeEdit

    signal_changed = QtCore.Signal(datetime.datetime)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # dateedit
        self._dateedit = QtWidgets.QDateEdit()
        self._dateedit.setDisplayFormat("yyyy/MM/dd")
        self._dateedit.setCalendarPopup(True)
        self._dateedit.dateChanged.connect(self.on_date_time_changed)
        layout.addWidget(self._dateedit)

        # timeedit
        self._timeedit = QtWidgets.QTimeEdit()
        self._timeedit.setDisplayFormat("hh:mm:ss")
        self._timeedit.timeChanged.connect(self.on_date_time_changed)
        self.set_date_time(datetime.datetime.now(), is_emit=False)

        layout.addWidget(self._timeedit)
        self.setLayout(layout)

    # public
    def set_date_time(self, dt: datetime.datetime, is_emit: bool = True) -> None:
        qdatetime: QtCore.QDateTime = datetime_to_qdatetime(dt)
        qdate: QtCore.QDate = qdatetime.date()
        qtime: QtCore.QTime = qdatetime.time()
        if is_emit:
            self._dateedit.setDate(qdate)
            self._timeedit.setTime(qtime)
        else:
            self._dateedit.blockSignals(True)
            self._dateedit.setDate(qdate)
            self._dateedit.blockSignals(False)
            self._timeedit.blockSignals(True)
            self._timeedit.setTime(qtime)
            self._timeedit.blockSignals(False)

    def date_time(self) -> datetime.datetime:
        qdate: QtCore.QDate = self._dateedit.date()
        qtime: QtCore.QTime = self._timeedit.time()
        qdatetime: QtCore.QDateTime = QtCore.QDateTime(qdate, qtime)
        return qdatetime_to_datetime(qdatetime)

    # handlers
    def on_date_time_changed(self):
        dt: datetime.datetime = self.date_time()
        self.signal_changed.emit(dt)


def qdatetime_to_datetime(qdatetime: QtCore.QDateTime) -> datetime.datetime:
    qdate: QtCore.QDate = qdatetime.date()
    qtime: QtCore.QTime = qdatetime.time()
    return datetime.datetime(
        year=qdate.year(),
        month=qdate.month(),
        day=qdate.day(),
        hour=qtime.hour(),
        minute=qtime.minute(),
        second=qtime.second(),
    )


def datetime_to_qdatetime(dt: datetime.datetime) -> QtCore.QDateTime:
    qdate: QtCore.QDate = QtCore.QDate(dt.year, dt.month, dt.day)
    qtime: QtCore.QTime = QtCore.QTime(dt.hour, dt.minute, dt.second)
    return QtCore.QDateTime(qdate, qtime)
