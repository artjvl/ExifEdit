from __future__ import annotations
import os
import send2trash
import datetime
from typing import Any, Optional, Union, BinaryIO, Callable

import exif


class Image(object):

    _path: str
    _size: int
    _img: exif.Image

    def __init__(self, path: str) -> None:
        assert os.path.isfile(path)
        self._path = path
        self._size = os.path.getsize(path)

        img_bytes: Union[BinaryIO, bytes, str]
        with open(path, "rb") as img_bytes:
            self._img = exif.Image(img_bytes)

    # protected
    def _exif_field(
        self,
        tag: str,
        func: Optional[Callable[[Any], Any]] = None,
    ) -> ExifField:
        value: Optional[Any] = None
        if self.has_exif(tag=tag):
            value = self._img.get(tag)
        if value is not None:
            parsed: Any = value
            if func is not None:
                parsed = func(value)
            return parsed
        return None

    def _check_path(self) -> bool:
        return os.path.isfile(self._path)

    def _add_suffix(self, path: str) -> str:
        dirname: str = os.path.dirname(path)
        filename: str = os.path.basename(path)
        basename: str = os.path.splitext(filename)[0]
        extension: str = os.path.splitext(filename)[1]
        i: int = 1
        while os.path.isfile(path):
            path = os.path.join(dirname, f"{basename}-{i}{extension}")
            i += 1
        return path

    # public
    def path(self) -> str:
        return self._path

    def dirname(self) -> str:
        return os.path.dirname(self._path)

    def filename(self) -> str:
        return os.path.basename(self._path)

    def basename(self) -> str:
        return os.path.splitext(os.path.basename(self._path))[0]

    def extension(self) -> str:
        return os.path.splitext(os.path.basename(self._path))[1]

    def has_exif(self, tag: Optional[str] = None) -> bool:
        has_exif_: bool = self._img.has_exif
        if tag is not None:
            has_exif_ = has_exif_ and hasattr(self._img, tag)
        return has_exif_

    def filesize_kb(self) -> float:
        return self._size / (1 << 10)

    def filesize_mb(self) -> float:
        return self._size / (1 << 20)

    def set_date_taken(self, dt: datetime.datetime) -> None:
        date_taken_string: str = dt.strftime("%Y:%m:%d %H:%M:%S")
        self._img.datetime = date_taken_string
        self._img.datetime_digitized = date_taken_string
        self._img.datetime_original = date_taken_string

    def date_taken(self) -> Optional[datetime.datetime]:
        return self._exif_field(
            "datetime",
            func=lambda s: datetime.datetime.strptime(
                s,
                "%Y:%m:%d %H:%M:%S",
            ),
        )

    def camera_maker(self) -> str:
        return self._exif_field("make")

    def camera_model(self) -> str:
        return self._exif_field("model")

    def lens_model(self) -> str:
        return self._exif_field("lens_model")

    def resolution(self) -> Optional[str]:
        resolution_x: Optional[int] = self._exif_field("pixel_x_dimension")
        resolution_y: Optional[int] = self._exif_field("pixel_y_dimension")
        orientation: int = self._exif_field("orientation")
        if (
            resolution_x is not None
            and resolution_y is not None
            and orientation is not None
        ):
            mp: int = (resolution_x * resolution_y) / (1e6)
            res: str = (
                f"{resolution_x}x{resolution_y}"
                if orientation == 1
                else f"{resolution_y}x{resolution_x}"
            )
            return f"{res} ({mp:.2f} MP)"

    def fstop(self) -> Optional[float]:
        return self._exif_field("f_number")

    def exp_time(self) -> Optional[int]:
        return self._exif_field("exposure_time", func=lambda f: int(round(1 / f)))

    def iso(self) -> Optional[int]:
        return self._exif_field("photographic_sensitivity")

    def focal_length(self) -> Optional[float]:
        return self._exif_field("focal_length")

    def save(self, filepath: Optional[str] = None, is_send2trash: bool = True) -> str:
        if filepath is None:
            filepath = self._path

        # rename old file
        assert self._check_path(), "Image file not found"
        if is_send2trash:
            send2trash.send2trash(self._path)
        else:
            os.remove(self._path)

        # save new file
        filepath = self._add_suffix(filepath)

        if filepath == self._path:
            print(f"Saving '{filepath}'")
        else:
            print(f"Saving '{self._path}' -> '{filepath}'")

        with open(filepath, "wb") as img_bytes:
            img_bytes.write(self._img.get_file())

        return filepath


class ExifField(object):
    _description: str
    _value: Optional[Any]
    _formatted_value: Optional[str]

    def __init__(
        self, description: str, value: Optional[Any], formatted_value: Optional[str]
    ) -> None:
        self._description = description
        self._value = value
        self._formatted_value = formatted_value

    def description(self) -> str:
        return self._description

    def value(self) -> Optional[Any]:
        return self._value

    def formatted_value(self) -> str:
        if self._formatted_value is not None:
            return self._formatted_value
        return ""
