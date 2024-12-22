from __future__ import annotations
import time
from typing import Optional, Type

from PySide6 import QtCore, QtGui, QtWidgets


class SquarePixLabel(QtWidgets.QLabel):

    _border: int  # border in px
    _is_busy: bool
    _thread: QtCore.QThread
    _loader: ImageLoader

    signal_done: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._border = 1
        self._is_busy = False

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

    def has_image(self) -> bool:
        return self.has_pixmap()

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

    def load_image(self, path: str) -> bool:
        # Loads an image from the given 'path'. Returns 'True' if the ImageLoader thread is started
        # successfully (i.e., 'self._is_busy' is false). Otherwise, 'False' is returned. 

        assert path != None    
        self.clear_image()

        if self._is_busy:
            # image-loading thread is busy loading an image; new image cannot be loaded
            return False

        self._is_busy = True

        # create 'QThread' instance 'self._thread'
        self._thread: QtCore.QThread = QtCore.QThread()
        
        # create 'ImageLoader' instance 'self._loader'
        self._loader: ImageLoader = self.image_loader()(
            path, self.inner_size(), time.time()
        )

        # move 'ImageLoader' object to thread for execution and event-handling 
        self._loader.moveToThread(self._thread)

        # connect handlers
        self._thread.started.connect(self._loader.run)
        self._loader.signal_image.connect(self.set_image)
        self._loader.signal_image.connect(self._thread.quit)
        self._loader.signal_image.connect(self._loader.deleteLater)

        # start thread
        self._thread.start()

        # return 'True' because the image-loading was successfully started
        return True

    def clear_image(self) -> None:
        self.clear()

    def image_loader(self) -> Type[ImageLoader]:
        return ImageLoader

    def set_image(self, pixmap: QtGui.QPixmap) -> None:
        # Handler method that sets the image loaded by the 'ImageLoader' on the separate thread
        # created by the 'load_image' method. This method is connected to the 'signal_image' signal
        # emitted by 'ImageLoader' once image-loading is complete.

        self._is_busy = False
        self.setPixmap(pixmap)
        self.signal_done.emit()


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
        return ImageLoader


class ImageLoader(QtCore.QObject):
    # ref: https://realpython.com/python-pyqt-qthread/

    signal_image: QtCore.Signal = QtCore.Signal(QtGui.QPixmap)
    _path: str
    _size: QtCore.QSize
    _t0: Optional[float]

    def __init__(
        self,
        path: str,
        size: QtCore.QSize,
        t0: Optional[float] = None,
        parent: Optional[QtCore.QObject] = None,
    ):
        super().__init__(parent)
        self._path = path
        self._size = size
        self._t0 = t0

    def run(self) -> None:
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
            f"{self._path} ({qimg_size.width()}x{qimg_size.height()}) [{t1 - t0:.6f} s]"
        )
        self.signal_image.emit(pixmap)

    def read_image(self, reader: QtGui.QImageReader) -> QtGui.QImage:
        img_size: QtCore.QSize = reader.size()
        transformation: QtGui.QImageIOHandler.Transformation = reader.transformation()
        is_rotated: bool = transformation in (
            QtGui.QImageIOHandler.Transformation.TransformationRotate90,
            QtGui.QImageIOHandler.Transformation.TransformationRotate270,
        )

        reduction_factor: float
        if not is_rotated:
            reduction_factor = min(
                self._size.width() / img_size.width(),
                self._size.height() / img_size.height(),
            )
        else:
            reduction_factor = min(
                self._size.width() / img_size.height(),
                self._size.height() / img_size.width(),
            )

        # reduction_factor: float = label_width / max(img_size.width(), img_size.height())
        qimg_size: QtCore.QSize = QtCore.QSize(
            round(reduction_factor * img_size.width()),
            round(reduction_factor * img_size.height()),
        )
        reader.setScaledSize(qimg_size)
        qimg: QtGui.QImage = reader.read()
        return qimg
