from __future__ import annotations
import os
import time
from typing import List, Optional

from PySide6 import QtCore, QtWidgets

from package.Image import Image, ImageExif, ImagePiexif
from package.FileEdit import FileEdit


class FileModify(QtWidgets.QWidget):

    _is_send2trash: bool

    _UPDATE_RATIO: float = 0.3
    _t_previous: float
    _t_delta: float

    _filepaths: List[str]
    _modified_filepaths: List[str]
    _file_edit: FileEdit

    _button_modify: QtWidgets.QPushButton
    _progress_bar: QtWidgets.QProgressBar
    _status_label: QtWidgets.QLabel
    _thread: Optional[QtCore.QThread]
    _modifier: Optional[FileModifier]

    signal_done: QtCore.Signal = QtCore.Signal(bool)

    def __init__(
        self, file_edit: FileEdit, parent: Optional[QtWidgets.QWidget]
    ) -> None:
        super().__init__(parent)
        self._thread = None
        self._modifier = None
        self._is_send2trash = True
        self._t_previous = 0.0
        self._t_delta = 0.0

        self._filepaths = []
        self._modified_filepaths = []
        self._file_edit = file_edit

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 6, 0, 0)
        self.setLayout(layout)

        button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        self._button_modify: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Modify files"
        )
        self._button_modify.setEnabled(False)
        self._button_modify.pressed.connect(self.on_modify_button_pressed)
        self._file_edit.signal_checked.connect(
            self.on_fileedit_checked
        )  # dependency: button-modify
        button_layout.addWidget(self._button_modify)

        self._button_stop: QtWidgets.QPushButton = QtWidgets.QPushButton("Stop")
        self._button_stop.pressed.connect(self.on_stop)
        self._button_stop.setEnabled(False)
        button_layout.addWidget(self._button_stop)

        buttons: QtWidgets.QWidget = QtWidgets.QWidget()
        buttons.setLayout(button_layout)
        layout.addWidget(buttons)

        self._progress_bar = QtWidgets.QProgressBar()
        layout.addWidget(self._progress_bar)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)

        self._items_label = QtWidgets.QLabel("")
        self._items_label.setAlignment(QtCore.Qt.AlignCenter)
        self._time_label = QtWidgets.QLabel("")
        self._time_label.setAlignment(QtCore.Qt.AlignCenter)
        status_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self._items_label, stretch=1)
        status_layout.addWidget(self._time_label, stretch=1)
        labels: QtWidgets.QWidget = QtWidgets.QWidget()
        labels.setLayout(status_layout)
        layout.addWidget(labels)

    def set_images(self, filepaths: List[str]) -> None:
        # Saves image file-paths and enables 'Modify files' button if file modifiers are enabled.

        assert len(filepaths) > 0
        self._filepaths = filepaths
        self._modified_filepaths = []
        is_checked_fileedit: bool = self._file_edit.is_checked()
        self._button_modify.setEnabled(is_checked_fileedit)

    def has_images(self) -> bool:
        # Returns whether image file-paths are saved.

        return len(self._filepaths) > 0

    def clear_images(self) -> None:
        # Clears all saved image file-paths and disables 'Modify files' button.

        self._filepaths = []
        self._button_modify.setEnabled(False)

    def update_progress(self, n: int) -> None:
        if n == 0:
            self._t_previous = time.time()
            self._button_stop.setEnabled(True)
        else:
            # percentage
            N: int = len(self._filepaths)
            percent = int(round(100 * n / N))

            # timing
            t_now: float = time.time()
            t_previous: float = self._t_previous
            t_delta: float = t_now - t_previous
            t_delta_filtered: float = (
                self._UPDATE_RATIO * t_delta
                + (1 - self._UPDATE_RATIO) * self._t_delta
            )
            t_remaining: float = (N - n) * t_delta_filtered

            total_seconds: int = round(t_remaining)
            hours = total_seconds // 3600
            total_seconds %= 3600
            minutes = total_seconds // 60
            seconds = total_seconds % 60

            self._progress_bar.setValue(percent)
            self._items_label.setText(
                f"{n}/{N} images modified"
            )
            self._time_label.setText(
                f"({hours:02d}:{minutes:02d}:{seconds:02d} remaining)"
            )

            self._t_previous = t_now
            self._t_delta = t_delta_filtered

    def clear_progress(self) -> None:
        self._button_stop.setEnabled(False)
        self._progress_bar.reset()
        self._items_label.setText("")
        self._time_label.setText("")

    def enable_send2trash(self, is_send2trash: bool) -> None:
        self._is_send2trash = is_send2trash

    # getters
    def filepaths(self) -> List[str]:
        return self._filepaths

    def modified_filepaths(self) -> List[str]:
        return self._modified_filepaths

    # handlers
    @QtCore.Slot()
    def on_fileedit_checked(self, is_enabled: bool) -> None:
        is_enabled_button: bool = len(self._filepaths) > 0 and is_enabled
        self._button_modify.setEnabled(is_enabled_button)

    @QtCore.Slot()
    def on_modifier_status(self, status: int) -> None:

        if status == 0:
            # disable modify button
            self._button_modify.setEnabled(False)
            
            # update progress
            self.update_progress(0)

            # emit signal not done
            self.signal_done.emit(False)
        
        elif status > 0:
            # update progress
            self.update_progress(status)
        
        elif status < 0:
            # extract new filepaths
            self._modified_filepaths = self._modifier.new_filepaths()
            
            # clean modifier
            self._modifier = None

            # clear progress bar
            self.clear_progress()

            # enable modify button
            self._button_modify.setEnabled(True)

            # emit signal done
            self.signal_done.emit(True)

    @QtCore.Slot()
    def on_modify_button_pressed(self) -> None:
        # Creates and runs file-modifier thread.

        self._thread: QtCore.QThread = QtCore.QThread()
        self._modifier: FileModifier = FileModifier(
            self._filepaths, self._file_edit, is_send2trash=self._is_send2trash
        )
        self._modifier.moveToThread(self._thread)
        self._thread.started.connect(self._modifier.run)
        self._modifier.signal_status.connect(self.on_modifier_status)
        self._modifier.signal_status.connect(
            lambda status: self._thread.quit() if status == -1 else None
        )
        self._modifier.signal_status.connect(
            lambda status: self._modifier.deleteLater() if status == -1 else None
        )
        print("Thread started")
        self._thread.start()

    @QtCore.Slot()
    def on_stop(self) -> None:
        assert self._modifier is not None
        self._modifier.stop()


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
        self._file_edit = file_edit

        self._filepaths = filepaths
        self._new_filepaths = []
        self._is_running = False

    def stop(self) -> None:
        assert self._is_running == True
        self._is_running = False

    def new_filepaths(self) -> List[str]:
        return self._new_filepaths

    def run(self) -> None:
        assert self._is_running == False
        
        self._is_running = True
        self.signal_status.emit(0)
        for i, filepath in enumerate(self._filepaths):
            if not self._is_running:
                break
            else:
                self.signal_status.emit(i)

                if os.path.isfile(filepath):
                    img: Image = ImagePiexif(filepath)
                    new_filename: Optional[str] = self._file_edit.convert_file(img)
                    if new_filename is not None:
                        new_filepath: str = os.path.join(img.dirname(), new_filename)
                        img.save_with_filename(
                            filepath=new_filepath, is_send2trash=self._is_send2trash
                        )
                        self._new_filepaths.append(new_filepath)
                else:
                    print(f"Cannot find file '{filepath}'")
        self.signal_status.emit(-1)
