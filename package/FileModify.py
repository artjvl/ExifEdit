from __future__ import annotations
import os
from typing import List, Optional
import re

from PySide6 import QtCore, QtWidgets

from package.ExifFile import ExifFile
from package.FileEdit import FileEdit


class FileModify(QtWidgets.QWidget):

    _paths: List[str]
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
        self._paths = []
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

    def set_images(self, paths: List[str]) -> None:
        self._paths = paths
        self.update_button()

    def update_progress(self, n: Optional[int]) -> None:
        if n is not None:
            # in progress
            N: int = len(self._paths)
            percent = int(round(100 * n / N))
            self._progress_bar.setValue(percent)
            self._status_label.setText(f"{n}/{N} images modified")
        else:
            # done
            self._progress_bar.reset()
            self._status_label.setText("")

    # handlers
    def update_button(self, is_enabled: Optional[bool] = None) -> None:
        if is_enabled is None:
            is_enabled: bool = len(self._paths) > 0 and self._file_edit.is_checked()
        self._button_modify.setEnabled(is_enabled)

    def on_status(self, status: int) -> None:
        n: Optional[int] = status
        if status >= 0:
            self.update_button(False)
            self.signal_done.emit(False)
        else:
            self.update_button(True)
            n = None
            self.signal_done.emit(True)
        self.update_progress(n)

    def on_modify(self) -> None:
        self._thread: QtCore.QThread = QtCore.QThread()
        self._modifier: FileModifier = FileModifier(self._paths, self._file_edit)
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

    _paths: List[str]
    _file_edit: FileEdit

    # 0 = started; 1 - n = running; -1 = done
    signal_status: QtCore.Signal = QtCore.Signal(int)

    def __init__(
        self,
        paths: List[str],
        file_edit: FileEdit,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._paths = paths
        self._file_edit = file_edit

    def run(self) -> None:
        self.signal_status.emit(0)
        for i, path in enumerate(self._paths):
            self.signal_status.emit(i)

            if os.path.isfile(path):
                file: ExifFile = ExifFile(path)
                new_filename: Optional[str] = self._file_edit.convert_file(file)
                if new_filename is not None:
                    basename: str = file.get_basename()
                    extension: str = file.get_extension()
                    match = re.match(r"(.+)-\d+$", basename)
                    if match:
                        basename = match.group(1)
                    filename: str = f"{basename}{extension}"

                    if new_filename != filename:
                        file.save(filename=new_filename)
            else:
                print(f"Cannot find file '{path}'")
        self.signal_status.emit(-1)
