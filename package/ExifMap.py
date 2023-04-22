import os
from typing import Optional
import datetime
import re

from package.Image import Image
from package.ChangeDateTaken import ChangeDateTaken


class ExifMap(object):
    _img: Optional[Image]
    _dt: Optional[datetime.datetime]

    def __init__(self, change_date_taken: ChangeDateTaken) -> None:
        self._img = None
        self._change_date_taken = change_date_taken

    # private
    def _fix_string(self, text: str, replacement: str = "-") -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", replacement, text)

    def _has_date_time(self) -> bool:
        return self._date_time is not None

    def _date_time(self, file: Image) -> Optional[datetime.datetime]:
        dt: Optional[datetime.datetime] = file.date_taken()
        new_dt: Optional[
            datetime.datetime
        ] = self._change_date_taken.convert_date_taken(dt)
        if new_dt is not None:
            return new_dt
        return dt

    # public
    def basename(self, img: Image) -> Optional[str]:
        filename_: Optional[str] = img.filename()
        if filename_ is not None:
            return os.path.splitext(filename_)[0]
        return None

    def year(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.year:0>4}"
        return None

    def month(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.month:0>2}"
        return None

    def day(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.day:0>2}"
        return None

    def hour(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.hour:0>2}"
        return None

    def minute(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.minute:0>2}"
        return None

    def second(self, img: Image) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(img)
        if dt is not None:
            return f"{dt.second:0>2}"
        return None

    def camera_maker(self, img: Image) -> Optional[str]:
        exif_value: Optional[str] = img.camera_maker()
        if exif_value is not None:
            return self._fix_string(exif_value)
        return None

    def camera_model(self, img: Image) -> Optional[str]:
        exif_value: Optional[str] = img.camera_model()
        if exif_value is not None:
            return self._fix_string(exif_value)
        return None

    def text_upto(self, img: Image, text: str, is_include: bool) -> Optional[str]:
        filename: Optional[str] = self.basename(img)
        if filename is not None:
            pos: int = filename.find(text)
            if pos >= 0:
                if is_include:
                    pos += len(text)
                return filename[:pos]
        return None

    def text_from(self, img: Image, text: str, is_include: bool) -> Optional[str]:
        filename: Optional[str] = self.basename(img)
        if filename is not None:
            pos: int = filename.find(text)
            if pos >= 0:
                if not is_include:
                    pos += len(text)
                return filename[pos:]
        return None
