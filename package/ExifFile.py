from __future__ import annotations
import os
import datetime
from typing import Any, Optional

from PIL import Image, ExifTags


class ExifFile(object):

    _path: Optional[str]
    _size: Optional[int]
    _img: Optional[Image.Image]
    _exif: Optional[Image.Exif]

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = path
        self._size = None
        self._exif = None

        if path is not None:
            assert os.path.isfile(path)

            self._size = os.path.getsize(path)
            self._img: Image.Image = Image.open(path)
            self._exif = self._img.getexif()

    def _get_exif_field(self, tag: str) -> Optional[Any]:
        if self.has_exif() and tag in self._exif:
            return self._exif[tag]
        return None

    def _get_filename(self) -> Optional[str]:
        if self.has_file():
            return self._path.split("\\")[-1]
        return None

    # public
    def has_file(self) -> bool:
        return self._path is not None

    def has_exif(self) -> bool:
        return self._exif is not None

    def path(self) -> ExifField:
        return ExifField("File path", self._path, self._path)

    def img(self) -> Optional[Image.Image]:
        return self._img

    def exif(self) -> Optional[Image.Exif]:
        return self._exif

    def save(self) -> None:
        assert self.has_file()
        exif: Optional[Image.Exif] = self._exif
        print(f"Saving {self._path}")
        self._img.save(self._path)

    def filename(self) -> ExifField:
        description: str = "File name"
        if self.has_file():
            filename_: str = self._get_filename()
            return ExifField("File name", filename_, filename_)
        return ExifField(description, None, None)

    def set_filename(self, filename_: str) -> None:
        if self.has_file():
            path: str = self._path
            new_path: str = path.replace(self._get_filename(), filename_)
            self._path = new_path

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
        self._exif[ExifTags.Base.DateTime.value] = date_taken_string
        self._exif[ExifTags.Base.DateTimeOriginal.value] = date_taken_string
        self._exif[ExifTags.Base.DateTimeDigitized.value] = date_taken_string

    def date_taken(self) -> ExifField:
        description: str = "Date taken"
        value: Optional[Any] = self._get_exif_field(
            ExifTags.Base.DateTime.value
        )  # 0x9003
        if value is not None:
            dt: datetime.datetime = datetime.datetime.strptime(
                str(value),
                "%Y:%m:%d %H:%M:%S",
            )
            return ExifField(description, dt, f"{dt}")
        return ExifField(description, None, None)

    def camera_maker(self) -> ExifField:
        description: str = "Camera maker"
        value: Optional[Any] = self._get_exif_field(ExifTags.Base.Make.value)  # 0x010F
        if value is not None:
            camera_maker_: str = str(value)
            return ExifField(description, camera_maker_, camera_maker_)
        return ExifField(description, None, None)

    def camera_model(self) -> ExifField:
        description: str = "Camera model"
        value: Optional[Any] = self._get_exif_field(ExifTags.Base.Model.value)  # 0x0110
        if value is not None:
            camera_model_: str = str(value)
            return ExifField(description, camera_model_, camera_model_)
        return ExifField(description, None, None)

    def fstop(self) -> ExifField:
        description: str = "F-stop"
        value: Optional[Any] = self._get_exif_field(
            ExifTags.Base.FNumber.value
        )  # 0x829D
        if value is not None:
            fstop_: float = float(value)
            return ExifField(description, fstop_, f"f/{fstop_}")
        return ExifField(description, None, None)

    def exp_time(self) -> ExifField:
        description: str = "Exposure time"
        value: Optional[Any] = self._get_exif_field(
            ExifTags.Base.ExposureTime.value
        )  # 0x829A
        if value is not None:
            exp_time_: int = int(round(1 / float(value)))
            return ExifField(description, exp_time_, f"1/{exp_time_} s")
        return ExifField(description, None, None)

    def iso(self) -> ExifField:
        description: str = "ISO speed"
        value: Optional[Any] = self._get_exif_field(
            ExifTags.Base.ISOSpeedRatings.value
        )  # 0x8827
        if value is not None:
            iso_: int = int(value)
            return ExifField(description, iso_, f"{iso_}")
        return ExifField(description, None, None)

    def focal_length(self) -> ExifField:
        description: str = "Focal length"
        value: Optional[Any] = self._get_exif_field(
            ExifTags.Base.FocalLength.value
        )  # 0x920A
        if value is not None:
            focal_length_: float = float(value)
            return ExifField(description, focal_length_, f"{focal_length_} mm")
        return ExifField(description, None, None)


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
