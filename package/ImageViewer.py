import os
import time
from typing import Optional, Dict, List

from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image, ExifTags, ImageQt

from package.PixLabel import SquarePixLabel, AspectPixLabel


class ImageViewer(QtWidgets.QWidget):
    _paths: List[str]
    _index: int

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

    def create_tree(self) -> QtWidgets.QTreeWidget:
        tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget(parent=self)
        tree.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0%); font-size: 8pt; border-style: none;"
        )
        tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        tree.setFocusPolicy(QtCore.Qt.NoFocus)
        tree.setIndentation(0)
        tree.setColumnCount(2)
        tree.setColumnWidth(0, 90)
        tree.setHeaderHidden(True)
        return tree

    def fill_tree(self, path: Optional[str] = None) -> None:
        fields: List[str] = [
            "File name",
            "File size",
            "Date taken",
            "Camera maker",
            "Camera model",
            "F-stop",
            "Exposure time",
            "ISO speed",
            "Focal length",
        ]
        values: List[str] = [""] * len(fields)
        if path is not None:
            img: Image = Image.open(path)
            img_exif: Optional[Image.Exif] = img._getexif()

            values[0] = path.split("/")[-1]  # File name
            values[1] = f"{os.path.getsize(path)/(1<<20):,.2f} MB"

            if img_exif is not None:
                values[2] = f"{img_exif.get(0x9003)}"  # Date taken
                values[3] = f"{img_exif.get(0x010F)}"  # Camera maker
                values[4] = f"{img_exif.get(0x0110)}"  # Camera model
                values[5] = f"f/{img_exif.get(0x829D)}"  # F-stop
                values[6] = f"1/{round(1 / img_exif.get(0x829A))}"  # Exposure time
                values[7] = f"{img_exif.get(0x8827)}"  # ISO speed
                values[8] = f"{img_exif.get(0x920A)} mm"  # focal length
        assert len(fields) == len(values)

        self._exif_tree.clear()
        for i, field in enumerate(fields):
            QtWidgets.QTreeWidgetItem(self._exif_tree, [f"{field}:", values[i]])

    def load_images(self, paths: List[str]) -> None:
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

        self.fill_tree(path)

        self.set_buttons(False)
        self._pixlabel.load_image(path)
