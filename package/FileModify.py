from typing import List, Optional
import re

from PySide6 import QtWidgets

from package.ExifFile import ExifFile
from package.FileEdit import FileEdit


class FileModify(QtWidgets.QWidget):

    _paths: List[str]
    _file_edit: FileEdit

    _button_modify: QtWidgets.QPushButton
    _progress_bar: QtWidgets.QProgressBar
    _status_label: QtWidgets.QLabel

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
        layout.addWidget(self._status_label)

        self.update_button()

    def set_images(self, paths: List[str]) -> None:
        self._paths = paths
        self.update_button()

    # handlers
    def update_button(self) -> None:
        is_modify: bool = len(self._paths) > 0 and self._file_edit.is_checked()
        self._button_modify.setEnabled(is_modify)

    def on_modify(self) -> None:
        print("modify")
        for path in self._paths:
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
