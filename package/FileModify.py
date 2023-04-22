from __future__ import annotations
import os
from typing import List, Optional
import re

from PySide6 import QtCore, QtWidgets

from package.Image import Image
from package.FileEdit import FileEdit


class FileModify(QtWidgets.QWidget):

    _is_send2trash: bool

    _filepaths: List[str]
    _new_filepaths: List[str]
    _file_edit: FileEdit

    _button_modify: QtWidgets.QPushButton
    _progress_bar: QtWidgets.QProgressBar
    _status_label: QtWidgets.QLabel
    _thread: QtCore.QThread
    _loader: FileModifier

    signal_done: QtCore.Signal = QtCore.Signal(bool)

    def __init__(
        self, file_edit: FileEdit, parent: Optional[QtWidgets.QWidget]
    ) -> None:
        super().__init__(parent)
        self._is_send2trash = True

        self._filepaths = []
        self._new_filepaths = []
        self._file_edit = file_edit
        self._file_edit.signal_checked.connect(self.update_button)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 6, 0, 0)

        self._button_modify = QtWidgets.QPushButton("Modify files")
        self._button_modify.pressed.connect(self.on_modify)
        layout.addWidget(self._button_modify)

        self._progress_bar = QtWidgets.QProgressBar()
        layout.addWidget(self._progress_bar)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)

        self._status_label = QtWidgets.QLabel("")
        self._status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._status_label)

        self.update_button()

    def set_images(self, filepaths: List[str]) -> None:
        self._filepaths = filepaths
        self.update_button()

    def update_progress(self, n: Optional[int]) -> None:
        if n is not None:
            # in progress
            N: int = len(self._filepaths)
            percent = int(round(100 * n / N))
            self._progress_bar.setValue(percent)
            self._status_label.setText(f"{n}/{N} images modified")
        else:
            # done
            self._progress_bar.reset()
            self._status_label.setText("")

    def enable_send2trash(self, is_send2trash: bool) -> None:
        self._is_send2trash = is_send2trash

    # getters
    def filepaths(self) -> List[str]:
        return self._filepaths

    def new_filepaths(self) -> List[str]:
        return self._new_filepaths

    # handlers
    @QtCore.Slot()
    def update_button(self, is_enabled: Optional[bool] = None) -> None:
        if is_enabled is None:
            is_enabled: bool = len(self._filepaths) > 0 and self._file_edit.is_checked()
        self._button_modify.setEnabled(is_enabled)

    @QtCore.Slot()
    def on_status(self, status: int) -> None:
        n: Optional[int] = status
        if status >= 0:
            self.update_button(False)
            self.signal_done.emit(False)
        else:
            self.update_button(True)
            self._new_filepaths = self._modifier.new_filepaths()
            self.signal_done.emit(True)
            n = None
        self.update_progress(n)

    @QtCore.Slot()
    def on_modify(self) -> None:
        self._thread: QtCore.QThread = QtCore.QThread()
        self._modifier: FileModifier = FileModifier(
            self._filepaths, self._file_edit, is_send2trash=self._is_send2trash
        )
        self._modifier.moveToThread(self._thread)
        self._thread.started.connect(self._modifier.run)
        self._modifier.signal_status.connect(self.on_status)
        self._modifier.signal_status.connect(
            lambda status: self._thread.quit() if status == -1 else None
        )
        self._modifier.signal_status.connect(
            lambda status: self._modifier.deleteLater() if status == -1 else None
        )
        self._thread.start()


class FileModifier(QtCore.QObject):

    _is_send2trash: bool

    _filepaths: List[str]
    _new_filepaths: List[str]
    _file_edit: FileEdit

    # 0 = started; 1 - n = running; -1 = done
    signal_status: QtCore.Signal = QtCore.Signal(int)

    def __init__(
        self,
        filepaths: List[str],
        file_edit: FileEdit,
        is_send2trash: bool = True,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._is_send2trash = is_send2trash
        self._filepaths = filepaths
        self._new_filepaths = []
        self._file_edit = file_edit

    def new_filepaths(self) -> List[str]:
        return self._new_filepaths

    def run(self) -> None:
        self.signal_status.emit(0)
        for i, filepath in enumerate(self._filepaths):
            self.signal_status.emit(i)

            if os.path.isfile(filepath):
                img: Image = Image(filepath)
                new_filename: Optional[str] = self._file_edit.convert_file(img)
                if new_filename is not None:
                    new_filepath: str = os.path.join(img.dirname(), new_filename)
                    img.save(filepath=new_filepath, is_send2trash=self._is_send2trash)
                    self._new_filepaths.append(new_filepath)
            else:
                print(f"Cannot find file '{filepath}'")
        self.signal_status.emit(-1)
