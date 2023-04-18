from typing import Optional, List

from PySide6 import QtCore, QtWidgets

from package.PixLabel import SquarePixLabel
from package.ExifFile import ExifFile, ExifField


class ImageViewer(QtWidgets.QWidget):

    _paths: List[str]
    _index: int

    signal_image_changed = QtCore.Signal(ExifFile)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._paths = []
        self._index = 0

        # pixlabel
        self._pixlabel: SquarePixLabel = SquarePixLabel(parent=self)
        self._pixlabel.signal_done.connect(self.update_buttons)

        # button_next
        self._button_next: QtWidgets.QPushButton = QtWidgets.QPushButton(
            text=">", parent=self
        )
        self._button_next.pressed.connect(self.next_image)

        # button_prev
        self._button_prev: QtWidgets.QPushButton = QtWidgets.QPushButton(
            text="<", parent=self
        )
        self._button_prev.pressed.connect(self.previous_image)

        # button_reload
        self._button_reload: QtWidgets.QPushButton = QtWidgets.QPushButton(
            text="Reload", parent=self
        )
        self._button_reload.pressed.connect(self.load_image)

        # disable buttons
        self.set_buttons(False)

        # exif_tree
        self._exif_tree: QtWidgets.QTreeWidget = self.create_tree()
        self.fill_tree()

        # layouts
        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pixlabel)

        button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self._button_prev, stretch=1)
        button_layout.addWidget(self._button_reload, stretch=2)
        button_layout.addWidget(self._button_next, stretch=1)
        layout.addItem(button_layout)

        layout.addWidget(self._exif_tree)
        self.setLayout(layout)
        # self.resize(self.sizeHint().width(), self.minimumHeight())

    def create_tree(self) -> QtWidgets.QTreeWidget:
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
        tree.setFixedHeight(160)
        return tree

    def fill_tree(self, file: Optional[ExifFile] = None) -> None:
        if file is None:
            file = ExifFile()  # empty ExifFile to get the field names

        fields: List[ExifField] = [
            file.filename(),
            file.filesize_mb(),
            file.date_taken(),
            file.camera_maker(),
            file.camera_model(),
            file.fstop(),
            file.exp_time(),
            file.iso(),
            file.focal_length(),
        ]

        self._exif_tree.clear()
        for field in fields:
            QtWidgets.QTreeWidgetItem(
                self._exif_tree, [field.description(), field.formatted_value()]
            )

    def set_images(self, paths: List[str]) -> None:
        if paths != self._paths:
            self._paths = paths
            self._index = 0
            self.update_buttons()
            self.load_image()

    def set_buttons(self, is_enabled: bool):
        self._button_next.setEnabled(is_enabled)
        self._button_prev.setEnabled(is_enabled)
        self._button_reload.setEnabled(is_enabled)

    def update_buttons(self):
        self._button_next.setEnabled(False)
        self._button_prev.setEnabled(False)
        self._button_reload.setEnabled(False)
        num_images: int = len(self._paths)
        if num_images > 0:
            self._button_reload.setEnabled(True)
            if num_images > 1:
                self._button_next.setEnabled(True)
                self._button_prev.setEnabled(True)

    def path(self) -> Optional[str]:
        num_paths: int = len(self._paths)
        if num_paths > 0:
            self._index: int = self._index % len(self._paths)
            return self._paths[self._index]
        return None

    def next_image(self) -> None:
        self._index += 1
        self.load_image()

    def previous_image(self) -> None:
        self._index -= 1
        self.load_image()

    def load_image(self) -> None:
        path: Optional[str] = self.path()
        # if path is None:
        #     self._button_reload.setText("Reload")
        # else:
        #     self._button_reload.setText(
        #         f"Reload ({self._index + 1}/{len(self._paths)})"
        #     )

        file: Optional[ExifFile] = None
        if path is not None:
            file = ExifFile(path)
        self.fill_tree(file)

        self.set_buttons(False)
        self._pixlabel.load_image(path)
        self.signal_image_changed.emit(file)
