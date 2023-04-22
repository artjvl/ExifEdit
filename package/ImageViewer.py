from typing import Optional, List, Any, Callable

from PySide6 import QtCore, QtWidgets

from package.PixLabel import SquarePixLabel
from package.Image import Image


class ImageViewer(QtWidgets.QWidget):

    _paths: List[str]
    _index: int

    signal_image_changed = QtCore.Signal(Image)

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
        self._exif_tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        self._exif_tree.setHeaderHidden(True)
        self._exif_tree.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0%); font-size: 8pt; border-style: none;"
        )
        self._exif_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._exif_tree.setFocusPolicy(QtCore.Qt.NoFocus)
        self._exif_tree.setIndentation(0)
        self._exif_tree.setColumnCount(2)
        self._exif_tree.setColumnWidth(0, 90)
        self._exif_tree.setFixedHeight(180)
        fields: List[str] = [
            "File path",
            "File size",
            "Date taken",
            "Camera maker",
            "Camera model",
            "Lens model",
            "F-stop",
            "Exposure time",
            "ISO speed",
            "Focal length",
        ]
        for field in fields:
            QtWidgets.QTreeWidgetItem(self._exif_tree, [field, ""])

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

    def _convert_field(
        self, value: Any, func: Optional[Callable[[Any], str]] = None
    ) -> str:
        if value is not None:
            if func is not None:
                return func(value)
            return value
        return ""

    def fill_tree(self, img: Optional[Image] = None) -> None:
        values: Optional[List[str]] = None
        if img is not None:
            values: List[str] = [
                img.filename(),
                f"{img.filesize_mb():.2f} MB",
                self._convert_field(img.date_taken(), lambda dt: str(dt)),
                self._convert_field(img.camera_maker()),
                self._convert_field(img.camera_model()),
                self._convert_field(img.lens_model()),
                self._convert_field(img.fstop(), lambda f: f"f/{f}"),
                self._convert_field(img.exp_time(), lambda i: f"1/{i} s"),
                self._convert_field(img.iso(), lambda i: f"ISO{i}"),
                self._convert_field(img.focal_length(), lambda f: f"{f} mm"),
            ]

            num_fields: int = self._exif_tree.topLevelItemCount()
            assert len(values) == num_fields

            for i in range(num_fields):
                item: QtWidgets.QTreeWidgetItem = self._exif_tree.topLevelItem(i)
                value: str = ""
                if values is not None:
                    value = values[i]
                    item.setText(1, value)
                    item.setToolTip(1, value)

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

        img: Optional[Image] = None
        if path is not None:
            img = Image(path)
        self.fill_tree(img)

        self.set_buttons(False)
        self._pixlabel.load_image(path)
        self.signal_image_changed.emit(img)
