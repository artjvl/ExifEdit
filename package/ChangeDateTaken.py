from __future__ import annotations
import datetime
from typing import Optional

from PySide6 import QtCore, QtWidgets

from package.ExifFile import ExifFile
from package.NestedList import NestedListItem


class ChangeDateTaken(QtWidgets.QWidget):

    _nested: NestedListItem
    _nested_relative: NestedListItem
    _nested_specific: NestedListItem
    _nested_name: NestedListItem
    _datetime_relative: RelativeDateTime
    _datetime_specific: SpecificDateTime
    _is_relative: bool
    _is_specific_changed: bool
    _file: Optional[ExifFile]

    signal_changed = QtCore.Signal(datetime.datetime)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._is_specific_changed = False
        self._file = None

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Change Date taken
        self._nested = NestedListItem(text="Change Date taken", is_exclusive=True)
        layout.addWidget(self._nested)
        self._nested.signal_checked.connect(
            lambda b: self.emit_date_time() if not b else None
        )

        self._datetime_relative = RelativeDateTime()
        self._datetime_relative.signal_changed.connect(self.emit_date_time)
        self._nested_relative = self._nested.add_child(
            "Relative to Date taken", self._datetime_relative
        )
        self._nested_relative.signal_checked.connect(
            lambda b: self.on_relative_checked() if b else None
        )
        self._is_relative = True

        self._datetime_specific = SpecificDateTime()
        self._datetime_specific.signal_changed.connect(self.on_specific_changed)
        self._nested_specific = self._nested.add_child(
            "Specific date/time", self._datetime_specific
        )
        self._nested_specific.signal_checked.connect(
            lambda b: self.on_specific_checked() if b else None
        )

    # public
    def is_checked(self) -> bool:
        return self._nested.is_checked()

    def set_file(self, file: Optional[ExifFile]) -> None:
        self._file = file
        if not self._is_specific_changed and self.has_exif_date_time():
            self._datetime_specific.set_date_time(self.exif_date_time(), is_emit=False)
        self.emit_date_time()

    def has_file(self) -> bool:
        return self._file is not None

    def has_exif_date_time(self) -> bool:
        return self.exif_date_time() is not None

    def exif_date_time(self) -> Optional[datetime.datetime]:
        if self.has_file():
            return self._file.date_taken().value()
        return None

    def relative(self) -> datetime.timedelta:
        return self._datetime_relative.time_delta()

    def specific(self) -> datetime.datetime:
        return self._datetime_specific.date_time()

    # handlers
    def on_relative_checked(self) -> None:
        self._is_relative = True
        self.emit_date_time()

    def on_specific_checked(self) -> None:
        self._is_relative = False
        self.emit_date_time()

    def emit_date_time(self) -> None:
        # relative
        if self.is_checked():
            if self.has_file() and not self._is_relative:
                dt: datetime.datetime = self.specific()
                print(f"specific: {dt}")
                self.signal_changed.emit(dt)
                return
            if self.has_exif_date_time():
                dt: datetime.datetime = self._datetime_relative.date_time(
                    self.exif_date_time()
                )
                print(f"time-delta: {dt} ({self.relative()})")
                self.signal_changed.emit(dt)
                return
        if self.has_file():
            self.signal_changed.emit(self.exif_date_time())
            return
        self.signal_changed.emit(None)

    def on_specific_changed(self) -> None:
        self._is_specific_changed = True
        self.emit_date_time()


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
