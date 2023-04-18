from __future__ import annotations
import os
import send2trash
import datetime
from typing import Any, Optional, Union, BinaryIO, Callable, Tuple

from PIL import Image, ExifTags
import exif


class ExifFile(object):

    _path: Optional[str]
    _size: Optional[int]
    _img: Optional[exif.Image]

    def __init__(self, path: Optional[str] = None) -> None:

        self._path = path
        self._size = None
        self._img = None

        if path is not None:
            assert os.path.isfile(path)

            self._size = os.path.getsize(path)

            img_bytes: Union[BinaryIO, bytes, str]
            with open(path, "rb") as img_bytes:
                self._img = exif.Image(img_bytes)

    def get_dirname(self) -> Optional[str]:
        if self.has_file():
            return os.path.dirname(self._path)
        return None

    def get_filename(self) -> Optional[str]:
        if self.has_file():
            return os.path.basename(self._path)
        return None

    def get_basename(self) -> Optional[str]:
        if self.has_file():
            return os.path.splitext(os.path.basename(self._path))[0]
        return None

    def get_extension(self) -> Optional[str]:
        if self.has_file():
            return os.path.splitext(os.path.basename(self._path))[1]
        return None

    def _get_exif_field(
        self,
        tag: str,
        description: str,
        func: Optional[Callable[[Any], Tuple[Any, str]]] = None,
    ) -> ExifField:
        value: Optional[Any] = None
        if self.has_exif(tag=tag):
            value = self._img.get(tag)
        if value is not None:
            parsed: Any = value
            formatted: str = str(value)
            if func is not None:
                parsed, formatted = func(value)

            return ExifField(description, parsed, formatted)
        return ExifField(description, None, None)

    def _check_path(self, path: str) -> str:
        dirname: str = os.path.dirname(path)
        filename: str = os.path.basename(path)
        basename: str = os.path.splitext(filename)[0]
        extension: str = os.path.splitext(filename)[1]
        i: int = 1
        while os.path.isfile(path):
            path = os.path.join(dirname, f"{basename}-{i}{extension}")
            i += 1
        return path

    def _func_exp_time(self, value: int) -> Tuple[int, str]:
        exp_time_: int = int(round(1 / float(value)))
        return (exp_time_, f"1/{exp_time_} s")

    def _func_date_taken(self, value: str) -> Tuple[datetime.datetime, str]:
        dt: datetime.datetime = datetime.datetime.strptime(
            value,
            "%Y:%m:%d %H:%M:%S",
        )
        return (dt, str(dt))

    # public
    def has_file(self) -> bool:
        return self._path is not None

    def has_exif(self, tag: Optional[str] = None) -> bool:
        has_exif_: bool = self._img is not None and self._img.has_exif
        if tag is not None:
            has_exif_ = has_exif_ and hasattr(self._img, tag)
        return has_exif_

    def save(self, filename: str) -> None:
        assert self.has_file() and os.path.isfile(self._path)

        # rename old file
        send2trash.send2trash(self._path)

        # save new file
        dirname: str = os.path.dirname(filename)
        if dirname == "":
            dirname = os.path.dirname(self._path)
        new_path = os.path.join(dirname, filename)
        new_path = self._check_path(new_path)
        if new_path is self._path:
            print(f"Saving {new_path}")
        else:
            print(f"Saving {self._path} -> {new_path}")

        with open(new_path, "wb") as img_bytes:
            img_bytes.write(self._img.get_file())

    def path(self) -> ExifField:
        return ExifField("File path", self._path, self._path)

    def filename(self) -> ExifField:
        filename_: Optional[str] = self.get_filename()
        return ExifField("File path", filename_, filename_)

    def filesize_kb(self) -> ExifField:
        description: str = "File Size"
        if self.has_file():
            size_kb: float = self._size / (1 << 10)
            return ExifField(description, size_kb, f"{size_kb:,.2f} kB")
        return ExifField(description, None, None)

    def filesize_mb(self) -> ExifField:
        description: str = "File Size"
        if self.has_file():
            size_mb: float = self._size / (1 << 20)
            return ExifField(description, size_mb, f"{size_mb:,.2f} MB")
        return ExifField(description, None, None)

    def set_date_taken(self, dt: datetime.datetime) -> None:
        date_taken_string: str = dt.strftime("%Y:%m:%d %H:%M:%S")
        self._img.datetime = date_taken_string
        self._img.datetime_digitized = date_taken_string
        self._img.datetime_original = date_taken_string

    def date_taken(self) -> ExifField:
        return self._get_exif_field("datetime", "Date taken", self._func_date_taken)

    def camera_maker(self) -> ExifField:
        return self._get_exif_field("make", "Camera maker")

    def camera_model(self) -> ExifField:
        return self._get_exif_field("model", "Camera model")

    def lens_model(self) -> ExifField:
        return self._get_exif_field("lens_model", "Lens model")

    def fstop(self) -> ExifField:
        return self._get_exif_field("f_number", "F-stop", lambda f: (f, f"f/{f}"))

    def exp_time(self) -> ExifField:
        return self._get_exif_field(
            "exposure_time", "Exposure time", self._func_exp_time
        )

    def iso(self) -> ExifField:
        return self._get_exif_field(
            "photographic_sensitivity", "ISO speed", lambda i: (i, f"ISO{i}")
        )

    def focal_length(self) -> ExifField:
        return self._get_exif_field(
            "focal_length", "Focal length", lambda f: (f, f"{f} mm")
        )


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
