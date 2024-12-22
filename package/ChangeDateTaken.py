from __future__ import annotations
import datetime
from typing import Optional

from PySide6 import QtCore, QtWidgets

from package.NestedList import NestedListItem
from package.constants import MIN_TEXTWIDGET_HEIGHT


class ChangeDateTaken(QtWidgets.QWidget):

    _SETTING: str = "timedelta"
    _settings: QtCore.QSettings
    _nested: NestedListItem
    _datetime_relative: RelativeDateTime
    _datetime_specific: SpecificDateTime
    _is_relative: bool
    _is_specific_changed: bool
    _dt: Optional[datetime.datetime]

    signal_changed = QtCore.Signal(datetime.datetime)

    def __init__(
        self, settings: QtCore.QSettings, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings

        td_seconds: int = 0
        if self._settings.contains(self._SETTING):
            setting: Optional[str] = self._settings.value(self._SETTING)
            if setting is not None:
                td_seconds = setting

        self._is_specific_changed = False
        self._dt = None

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Change Date taken
        self._nested = NestedListItem(text="Change Date taken", is_exclusive=True)
        layout.addWidget(self._nested)
        self._nested.signal_checked.connect(
            lambda b: self.emit_date_time() if not b else None
        )

        self._datetime_relative = RelativeDateTime(total_seconds=td_seconds)
        self._datetime_relative.signal_changed.connect(self.on_relative_changed)
        nested_relative = self._nested.add_child(
            "Relative to Date taken", self._datetime_relative
        )
        nested_relative.signal_checked.connect(
            lambda b: self.on_relative_checked() if b else None
        )
        self._is_relative = True

        self._datetime_specific = SpecificDateTime()
        self._datetime_specific.signal_changed.connect(self.on_specific_changed)
        nested_specific = self._nested.add_child(
            "Specific date/time", self._datetime_specific
        )
        nested_specific.signal_checked.connect(
            lambda b: self.on_specific_checked() if b else None
        )

    # public
    def is_checked(self) -> bool:
        return self._nested.is_checked()

    def set_date_taken(self, dt: Optional[datetime.datetime]) -> None:
        self._dt = dt
        if dt is not None and not self._is_specific_changed:
            self._datetime_specific.set_date_time(dt, is_emit=False)
        self.emit_date_time()

    def has_date_taken(self) -> bool:
        return self._dt is not None

    def relative(self) -> datetime.timedelta:
        return self._datetime_relative.time_delta()

    def specific(self) -> datetime.datetime:
        return self._datetime_specific.date_time()

    def convert_date_taken(
        self, dt: Optional[datetime.datetime]
    ) -> Optional[datetime.datetime]:
        if self.is_checked():
            if not self._is_relative:
                # relative date
                new_dt: datetime.datetime = self.specific()
                return new_dt
            elif dt is not None:
                # specific date
                new_dt: datetime.datetime = self._datetime_relative.date_time(dt)
                return new_dt
        return None

    # emit
    def emit_date_time(self) -> None:
        dt: Optional[datetime.datetime] = self.convert_date_taken(self._dt)
        if dt is None and self._dt is not None:
            # date time is not changed
            dt = self._dt
        self.signal_changed.emit(dt)

    # handlers
    def on_relative_checked(self) -> None:
        self._is_relative = True
        self.emit_date_time()

    def on_relative_changed(self, td: datetime.timedelta) -> None:
        self._settings.setValue(self._SETTING, int(td.total_seconds()))
        self.emit_date_time()

    def on_specific_checked(self) -> None:
        self._is_relative = False
        self.emit_date_time()

    def on_specific_changed(self) -> None:
        self._is_specific_changed = True
        self.emit_date_time()


class RelativeDateTime(QtWidgets.QWidget):

    signal_changed = QtCore.Signal(datetime.timedelta)

    def __init__(
        self, total_seconds: int = 0, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)

        days = total_seconds // (24 * 3600)
        total_seconds %= 24 * 3600
        hours = total_seconds // 3600
        total_seconds %= 3600
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # combobox +/-
        self._combobox_pm = QtWidgets.QComboBox()
        self._combobox_pm.addItems(["+", "-"])
        self._combobox_pm.setMaximumWidth(50)
        self._combobox_pm.currentIndexChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._combobox_pm)

        # spinbox day(s)
        self._spinbox_days = QtWidgets.QSpinBox()
        self._spinbox_days.setValue(days)
        self._spinbox_days.setMaximumWidth(50)
        self._spinbox_days.setMinimumHeight(MIN_TEXTWIDGET_HEIGHT)
        self._spinbox_days.valueChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._spinbox_days)
        label_days = QtWidgets.QLabel("day(s)")
        label_days.setMaximumWidth(40)
        label_days.setMinimumHeight(MIN_TEXTWIDGET_HEIGHT)
        layout.addWidget(label_days)

        # timeedit relative
        self._timeedit_relative = QtWidgets.QTimeEdit()
        self._timeedit_relative.setMinimumHeight(MIN_TEXTWIDGET_HEIGHT)
        self._timeedit_relative.setDisplayFormat("hh:mm:ss")
        self._timeedit_relative.setTime(QtCore.QTime(hours, minutes, seconds))
        self._timeedit_relative.timeChanged.connect(
            lambda: self.signal_changed.emit(self.time_delta())
        )
        layout.addWidget(self._timeedit_relative)

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
        self._dateedit.setFixedHeight(MIN_TEXTWIDGET_HEIGHT)
        # print(f'date-edit height: {self._dateedit.sizeHint().height()}')
        self._dateedit.setDisplayFormat("yyyy/MM/dd")
        self._dateedit.setCalendarPopup(True)
        self._dateedit.dateChanged.connect(self.on_date_time_changed)
        layout.addWidget(self._dateedit)

        # timeedit
        self._timeedit = QtWidgets.QTimeEdit()
        self._timeedit.setMinimumHeight(MIN_TEXTWIDGET_HEIGHT)
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
