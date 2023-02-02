from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
from typing import Optional, Type
import time


class SquarePixLabel(QtWidgets.QLabel):
    signal_done: QtCore.Signal = QtCore.Signal()
    _border: int  # border in px

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._border = 1

        # style
        self.setStyleSheet(f"border: {self._border}px solid black;")

        # alignment
        self.setAlignment(QtCore.Qt.AlignCenter)

        # size policy
        self.setMinimumSize(1, 1)
        size_policy: QtWidgets.QSizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)

    def heightForWidth(self, width: int) -> int:
        return width

    def has_pixmap(self) -> bool:
        return not self.pixmap().isNull()

    def inner_size(self) -> QtCore.QSize:
        return QtCore.QSize(self.inner_width(), self.inner_height())

    def inner_width(self) -> int:
        return self.width() - 2 * self._border

    def inner_height(self) -> int:
        return self.height() - 2 * self._border

    def image_size(self) -> QtCore.QSize:
        assert self.has_pixmap()
        return self.pixmap().size()

    # def resizeEvent(self, event):
    #     # ref: https://stackoverflow.com/questions/44505229/pyqt-automatically-resizing-widget-picture
    #     super().resizeEvent(event)
    #     pixmap: QtGui.QPixmap = self.pixmap()
    #     if not pixmap.isNull():
    #         side: int = self.inner_width()
    #         scale: float = side / max(pixmap.width(), pixmap.height())
    #         new_size: QSize = QSize(scale * pixmap.width(), scale * pixmap.height())

    #         painter: QtGui.QPainter = QtGui.QPainter(self)
    #         painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    #         painter.drawPixmap(self.rect(), pixmap)

    #         self.setPixmap(
    #             pixmap.scaled(
    #                 new_size.width(),
    #                 new_size.height(),
    #                 Qt.IgnoreAspectRatio,
    #                 Qt.SmoothTransformation,
    #             )
    #         )

    def load_image(self, path: Optional[str]) -> None:
        self.clear()
        if path is not None:
            self.thread = QtCore.QThread()
            self.loader = self.image_loader()(path, self.inner_size(), time.time())
            self.loader.moveToThread(self.thread)
            self.thread.started.connect(self.loader.run)
            self.loader.signal_image.connect(self.set_image)
            self.loader.signal_image.connect(self.thread.quit)
            self.loader.signal_image.connect(self.loader.deleteLater)
            self.thread.start()

    def image_loader(self) -> Type[ImageLoader]:
        return ImageLoader

    def set_image(self, pixmap: QtGui.QPixmap) -> None:
        self.setPixmap(pixmap)
        self.signal_done.emit()


class ImageLoader(QtCore.QObject):
    # ref: https://realpython.com/python-pyqt-qthread/

    signal_image: QtCore.Signal = QtCore.Signal(QtGui.QPixmap)
    _path: str
    _size: QtCore.QSize
    _t0: Optional[float]

    def __init__(self, path: str, size: QtCore.QSize, t0: Optional[float] = None):
        super().__init__()
        self._path = path
        self._size = size
        self._t0 = t0

    def run(self):
        t0: Optional[None] = self._t0
        if t0 is None:
            t0 = time.time()

        reader: QtGui.QImageReader = QtGui.QImageReader(self._path)
        reader.setAutoTransform(True)
        qimg: QtGui.QImage = self.read_image(reader)
        pixmap: QtGui.QPixmap = QtGui.QPixmap.fromImage(qimg)

        t1 = time.time()
        qimg_size: QtCore.QSize = qimg.size()
        print(
            f"QImageReader -> QPixmap({qimg_size.width()}x{qimg_size.height()}) [{t1 - t0} s]"
        )
        self.signal_image.emit(pixmap)

    def read_image(self, reader: QtGui.QImageReader) -> QtGui.QImage:
        img_size: QtCore.QSize = reader.size()
        label_width: int = self._size.width()
        reduction_factor: float = label_width / max(img_size.width(), img_size.height())
        qimg_size: QtCore.QSize = QtCore.QSize(
            round(reduction_factor * img_size.width()),
            round(reduction_factor * img_size.height()),
        )
        reader.setScaledSize(qimg_size)
        qimg: QtGui.QImage = reader.read()
        return qimg


class AspectPixLabel(SquarePixLabel):
    _default_aspect_ratio: float

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._default_aspect_ratio = 1
        self.setScaledContents(True)

    def aspect_ratio(self) -> float:
        if self.has_pixmap():
            pixmap: QtGui.QPixmap = self.pixmap()
            return pixmap.width() / pixmap.height()
        return self._default_aspect_ratio

    def heightForWidth(self, width: int) -> int:
        return width / self.aspect_ratio()

    def image_loader(self) -> Type[ImageLoader]:
        return AspectImageLoader


class AspectImageLoader(ImageLoader):
    def read_image(self, reader: QtGui.QImageReader) -> QtGui.QImage:
        img_size: QtCore.QSize = reader.size()
        aspect_ratio: float = img_size.width() / img_size.height()

        # apply exif transformation to image
        transformation: QtGui.QImageIOHandler.Transformation = reader.transformation()
        is_rotated: bool = transformation in (
            QtGui.QImageIOHandler.Transformation.TransformationRotate90,
            QtGui.QImageIOHandler.Transformation.TransformationRotate270,
        )

        # read image based on QLabel size with correct aspect ratio
        label_width: int = self._size.width()
        qimg_size: QtCore.QSize
        if not is_rotated:
            qimg_size = QtCore.QSize(label_width, label_width / aspect_ratio)
        else:
            qimg_size = QtCore.QSize(label_width * aspect_ratio, label_width)
        reader.setScaledSize(qimg_size)
        qimg: QtGui.QImage = reader.read()
        return qimg
