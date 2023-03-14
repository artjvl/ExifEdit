from __future__ import annotations
import os
import datetime
from typing import List, Dict, Callable, Any, Optional

from PIL import Image


class ExifFile(object):

    _path: Optional[str]  # path
    _size: Optional[int]  # file size
    _date_taken: Optional[datetime.datetime]  # date taken
    _camera_maker: Optional[str]  # camera maker
    _camera_model: Optional[str]  # camera model
    _fstop: Optional[float]  # F-stop [f/n mm]
    _exp_time: Optional[int]  # exposure time [1/n s]
    _iso: Optional[int]  # ISO [-]
    _focal_length: Optional[float]  # focal length [mm]
    _has_exif: bool

    def __init__(self, path: Optional[str] = None) -> None:
        # file attributes
        self._path = path
        self._size = None

        # exif attributes
        self._date_taken = None
        self._camera_maker = None
        self._camera_model = None
        self._fstop = None
        self._exp_time = None
        self._iso = None
        self._focal_length = None

        if path is not None:
            self._size = os.path.getsize(path)

            img: Image = Image.open(path)
            img_exif: Optional[Image.Exif] = img._getexif()
            self._has_exif = False
            if img_exif is not None:
                self._has_exif = True

                self._date_taken = datetime.datetime.strptime(
                    str(img_exif.get(0x9003)), "%Y:%m:%d %H:%M:%S"
                )
                self._camera_maker = str(img_exif.get(0x010F))
                self._camera_model = str(img_exif.get(0x0110))
                self._fstop = float(img_exif.get(0x829D))
                self._exp_time = int(round(1 / float(img_exif.get(0x829A))))
                self._iso = int(img_exif.get(0x8827))
                self._focal_length = float(img_exif.get(0x920A))

    def path(self) -> ExifField:
        return ExifField("File path", self._path, lambda s: s)

    def filename(self) -> ExifField:
        name: Optional[str] = None
        if self._path is not None:
            name = self._path.split("/")[-1]
        return ExifField("File name", name, lambda s: s)

    def filesize_kb(self) -> ExifField:
        size_kb: Optional[int] = None
        if self._size is not None:
            size_kb = self._size / (1 << 10)
        return ExifField("File size", size_kb, lambda s: f"{s:,.2f} kB")

    def filesize_mb(self) -> ExifField:
        size_mb: Optional[int] = None
        if self._size is not None:
            size_mb = self._size / (1 << 20)
        return ExifField("File size", size_mb, lambda s: f"{s:,.2f} MB")

    def date_taken(self) -> ExifField:
        return ExifField("Date taken", self._date_taken, lambda s: f"{s}")

    def camera_maker(self) -> ExifField:
        return ExifField("Camera maker", self._camera_maker, lambda s: s)

    def camera_model(self) -> ExifField:
        return ExifField("Camera model", self._camera_model, lambda s: s)

    def fstop(self) -> ExifField:
        return ExifField("F-stop", self._fstop, lambda s: f"f/{s}")

    def exp_time(self) -> ExifField:
        return ExifField("Exposure time", self._exp_time, lambda s: f"1/{s} s")

    def iso(self) -> ExifField:
        return ExifField("ISO speed", self._iso, lambda s: f"{s}")

    def focal_length(self) -> ExifField:
        return ExifField("Focal length", self._focal_length, lambda s: f"{s} mm")

    def has_exif(self) -> bool:
        return self._has_exif


class ExifField(object):
    _title: str
    _value: Any
    _format: Callable[[Any], str]

    def __init__(self, title: str, value: Any, format: Callable[[Any], str]) -> None:
        self._title = title
        self._value = value
        self._format = format

    def title(self) -> str:
        return self._title

    def value(self) -> Any:
        return self._value

    def set_value(self, value: Any) -> None:
        self._value = value

    def print(self) -> str:
        if self._value is not None:
            return self._format(self._value)
        return ""
