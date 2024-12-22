from __future__ import annotations
import os
import abc
import send2trash
import datetime
from typing import Any, Optional, Dict, Tuple, Union, BinaryIO, Callable

import exif
import piexif
from PIL import Image as PILImage


class Image(object):

    __metaclass__ = abc.ABCMeta

    _path: str
    _size: int

    def __init__(self, path: str) -> None:
        assert os.path.isfile(path)
        self._path = path
        self._size = os.path.getsize(path)

    # protected
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

    @abc.abstractmethod
    def has_exif(self, tag: Optional[str] = None) -> bool:
        return

    def filesize_kb(self) -> float:
        return self._size / (1 << 10)

    def filesize_mb(self) -> float:
        return self._size / (1 << 20)

    @abc.abstractmethod
    def resolution(self) -> Tuple[int, int]:
        return

    @abc.abstractmethod
    def set_date_taken(self, dt: datetime.datetime) -> None:
        return
    
    @abc.abstractmethod
    def date_taken(self) -> Optional[datetime.datetime]:
        return

    @abc.abstractmethod
    def camera_maker(self) -> Optional[str]:
        return

    @abc.abstractmethod
    def camera_model(self) -> Optional[str]:
        return

    @abc.abstractmethod
    def lens_model(self) -> Optional[str]:
        return

    @abc.abstractmethod
    def fstop(self) -> Optional[float]:
        return

    @abc.abstractmethod
    def exp_time(self) -> Optional[float]:
        return

    @abc.abstractmethod
    def iso(self) -> Optional[int]:
        return

    @abc.abstractmethod
    def focal_length(self) -> Optional[float]:
        return

    @abc.abstractmethod
    def save(self, filepath: Optional[str] = None, is_send2trash: bool = True) -> str:
        return


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


class ImageExif(Image):

    _img: exif.Image

    def __init__(self, path: str) -> None:
        super().__init__(path)

        # read image as bytes using exif library
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
    
    # public 
    def has_exif(self, tag: Optional[str] = None) -> bool:
        has_exif_: bool = self._img.has_exif
        if tag is not None:
            has_exif_ = has_exif_ and hasattr(self._img, tag)
        return has_exif_

    def resolution(self) -> Tuple[int, int]:
        resolution_1: int = self._exif_field("pixel_x_dimension")
        resolution_2: int = self._exif_field("pixel_y_dimension")
        orientation: int = self._exif_field("orientation")
        
        resolution_x: int = resolution_1
        resolution_y: int = resolution_2
        if orientation != 1:
            resolution_x = resolution_2
            resolution_y = resolution_1
        return (resolution_x, resolution_y)

    def set_date_taken(self, dt: datetime.datetime) -> None:
        date_taken_string: str = dt.strftime("%Y:%m:%d %H:%M:%S")
        self._img.datetime = date_taken_string
        self._img.datetime_digitized = date_taken_string
        self._img.datetime_original = date_taken_string

    def date_taken(self) -> Optional[datetime.datetime]:
        return self._exif_field(
            "datetime_original",
            func=lambda s: datetime.datetime.strptime(
                s,
                "%Y:%m:%d %H:%M:%S",
            ),
        )

    def camera_maker(self) -> Optional[str]:
        return self._exif_field("make")

    def camera_model(self) -> Optional[str]:
        return self._exif_field("model")

    def lens_model(self) -> Optional[str]:
        return self._exif_field("lens_model")

    def fstop(self) -> Optional[float]:
        return self._exif_field("f_number")

    def exp_time(self) -> Optional[float]:
        exp_time: Optional[float] = self._exif_field("exposure_time")
        if exp_time is not None:
            return exp_time
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


class ImagePiexif(Image):

    _img: PILImage
    _exif_data: Dict[str, Any]

    def __init__(self, path: str) -> None:
        super().__init__(path)

        self._img = PILImage.open(path)
        self._exif_data = piexif.load(path)

        # bugfix
        if 41729 in self._exif_data["Exif"]:
            self._exif_data["Exif"][41729] = b'\x01'
    
    # public 
    def resolution(self) -> Tuple[int, int]:
        resolution_1: int = self._img.width
        resolution_2: int = self._img.height
        orientation: int = self._exif_data["0th"].get(piexif.ImageIFD.Orientation, 1)
        
        resolution_x: int = resolution_1
        resolution_y: int = resolution_2
        if orientation > 4:
            resolution_x = resolution_2
            resolution_y = resolution_1
        return (resolution_x, resolution_y)

    def set_date_taken(self, dt: datetime.datetime) -> None:
        date_taken_string: str = dt.strftime("%Y:%m:%d %H:%M:%S")
        self._exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_taken_string.encode("utf-8")
        self._exif_data["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_taken_string.encode("utf-8")

    def date_taken(self) -> Optional[datetime.datetime]:
        date_taken_str: Optional[str] = self._exif_data["Exif"].get(piexif.ExifIFD.DateTimeOriginal, None)
        if date_taken_str is not None:
            return datetime.datetime.strptime(date_taken_str.decode(), "%Y:%m:%d %H:%M:%S")
        return None

    def camera_maker(self) -> Optional[str]:
        camera_maker: Optional[str] = self._exif_data["0th"].get(piexif.ImageIFD.Make, None)
        if camera_maker is not None:
            return camera_maker.decode()
        return None

    def camera_model(self) -> Optional[str]:
        camera_model: Optional[str] = self._exif_data["0th"].get(piexif.ImageIFD.Model, None)
        if camera_model is not None:
            return camera_model.decode()
        return None

    def lens_model(self) -> Optional[str]:
        lens_model: Optional[str] = self._exif_data["Exif"].get(piexif.ExifIFD.LensModel, None)
        if lens_model is not None:
            return lens_model.decode()
        return None

    def fstop(self) -> Optional[float]:
        fstop: Optional[Tuple[int, int]] = self._exif_data["Exif"].get(piexif.ExifIFD.FNumber, None)
        if fstop is not None:
            return fstop[0] / fstop[1]
        return None

    def exp_time(self) -> Optional[float]:
        exp_time: Optional[Tuple[int, int]] = self._exif_data["Exif"].get(piexif.ExifIFD.ExposureTime, None)
        if exp_time is not None:
            return exp_time[0] / exp_time[1]
        return None

    def iso(self) -> Optional[int]:
        return self._exif_data["Exif"].get(piexif.ExifIFD.ISOSpeedRatings, None)

    def focal_length(self) -> Optional[float]:
        focal_length = self._exif_data["Exif"].get(piexif.ExifIFD.FocalLength, None)
        if focal_length is not None:
            return focal_length[0] / focal_length[1]
        return None

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

        exif_bytes: bytes = piexif.dump(self._exif_data)
        self._img.save(filepath, "jpeg", exif=exif_bytes)

        return filepath