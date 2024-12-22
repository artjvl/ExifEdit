from typing import Optional, List, Tuple, Any, Callable

from PySide6 import QtCore, QtWidgets

from package.PixLabel import SquarePixLabel
from package.Image import Image, ImageExif, ImagePiexif


class ImageViewer(QtWidgets.QWidget):

    _path: Optional[str]
    _is_buttons_enabled: bool

    signal_image_cycle_next = QtCore.Signal(bool)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self._path = None
        self._is_buttons_enabled = True

        # pixlabel
        self._pixlabel: SquarePixLabel = SquarePixLabel(parent=self)
        self._pixlabel.signal_done.connect(self.on_pixlabel_done)

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
        self._button_reload.pressed.connect(lambda: self._pixlabel.load_image(self._path))

        # disable buttons
        self.enable_buttons(False)

        # exif_tree
        self._exif_tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        self._exif_tree.setHeaderHidden(True)
        self._exif_tree.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0%); font-size: 10pt; border-style: none;"
        )
        self._exif_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._exif_tree.setFocusPolicy(QtCore.Qt.NoFocus)
        self._exif_tree.setIndentation(0)
        self._exif_tree.setColumnCount(2)
        self._exif_tree.setColumnWidth(0, 90)
        self._exif_tree.setFixedHeight(192)
        fields: List[str] = [
            "File path",
            "File size",
            "Resolution",
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

    def _format_field(self, values: List[Any], format: Optional[str] = None) -> str:
        # Converts EXIF value to formatted string. Example: with EXIF F-stop = 2.8, the formatted
        # string is 'f/2.8'. If the EXUF value is 'None', the formatted string is empty.

        if all(item is None for item in values):
            return ""
        try:
            # If fmt is provided, use it. Otherwise, just convert the value to a string.
            return format.format(*values) if format else ' '.join(map(str, values))
        except (ValueError, TypeError):
            return ""

    def _fill_tree(self, img: Image) -> None:
        # Fills the EXIF value tree with formatted strings extracted from the image.

        # resolution
        resolution_x: int
        resolution_y: int
        [resolution_x, resolution_y] = img.resolution()

        # exposure time
        exp_time_formatted: str = ''
        exp_time: Optional[float] = img.exp_time()
        if exp_time is not None:
            if exp_time < 1:
                exp_time_formatted = f"1/{int(round(1 / exp_time))} s"
            else:
                exp_time_formatted = f"{exp_time:.1f} s"

        # format all values into strings
        values: List[str] = [
            self._format_field([img.filename()]),
            self._format_field([img.filesize_mb(), img.filesize_kb()], '{:.2f} MB ({:.1f} KB)'),
            self._format_field([resolution_x, resolution_y, (resolution_x * resolution_y) / 1e6], '{}x{} ({:.2f} MP)'),
            self._format_field([img.date_taken()], '{}'),
            self._format_field([img.camera_maker()]),
            self._format_field([img.camera_model()]),
            self._format_field([img.lens_model()]),
            self._format_field([img.fstop()], 'f/{}'),
            self._format_field([exp_time_formatted]),
            self._format_field([img.iso()], 'ISO{}'),
            self._format_field([img.focal_length()], '{} mm'),
        ]

        num_fields: int = self._exif_tree.topLevelItemCount()
        assert len(values) == num_fields

        # fill tree with formatted strings
        for i in range(num_fields):
            item: QtWidgets.QTreeWidgetItem = self._exif_tree.topLevelItem(i)
            value: str = ""
            if values is not None:
                value = values[i]
                item.setText(1, value)
                item.setToolTip(1, value)

    def _clear_tree(self) -> None:
        # Clears EXIF value tree.
        
        num_fields: int = self._exif_tree.topLevelItemCount()
        for i in range(num_fields):
            item: QtWidgets.QTreeWidgetItem = self._exif_tree.topLevelItem(i)
            item.setText(1, "")
            item.setToolTip(1, "")

    def enable_buttons(self, is_enabled: bool) -> None:
        self._is_buttons_enabled = is_enabled
        self._button_next.setEnabled(is_enabled)
        self._button_prev.setEnabled(is_enabled)

    def has_image(self) -> bool:
        return self._pixlabel.has_image()

    def next_image(self) -> None:
        self.signal_image_cycle_next.emit(True)

    def previous_image(self) -> None:
        self.signal_image_cycle_next.emit(False)

    def load_image(self, path: str) -> Image:
        # Returns the image object with EXIF values extracted for the provided path. The function
        # fills the EXIF tree and initiating image-loading in the PixLabel.

        assert path != None

        self._path = path
        img = ImagePiexif(path)
        self._fill_tree(img)
        self._button_next.setEnabled(False)
        self._button_prev.setEnabled(False)
        self._pixlabel.load_image(path)
        return img

    def clear(self) -> None:
        # Clears image.

        self._clear_tree()
        self._button_reload.setEnabled(False)
        self.enable_buttons(False)
        if self._pixlabel.has_image():
            self._pixlabel.clear_image()

    # handlers
    QtCore.Slot()
    def on_pixlabel_done(self):
        self._button_reload.setEnabled(True)
        self._button_next.setEnabled(self._is_buttons_enabled)
        self._button_prev.setEnabled(self._is_buttons_enabled)
