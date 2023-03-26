from typing import Optional
import datetime
import re

from package.ExifFile import ExifFile


class ExifMap(object):
    _file: Optional[ExifFile]
    _dt: Optional[datetime.datetime]

    def __init__(self) -> None:
        self._file = None
        self._dt = None

    # private
    def _fix_string(self, text: str, replacement: str = "-") -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", replacement, text)

    def _has_file(self) -> bool:
        return self._file is not None

    def _has_date_time(self) -> bool:
        return self._date_time is not None

    def _date_time(self) -> Optional[datetime.datetime]:
        if self._has_file():
            if self._dt is not None:
                return self._dt
            dt: Optional[datetime.datetime] = self._file.date_taken().value()
            if dt is not None:
                return dt
        return None

    def _filename(self) -> Optional[str]:
        if self._has_file():
            filename: str = self._file.filename().value()
            return filename.rsplit(".", 1)[0]
        return None

    # public
    def set_file(self, exif_file: Optional[ExifFile]) -> None:
        self._file = exif_file

    def set_date_time(self, dt: Optional[datetime.datetime]) -> None:
        self._dt = dt

    def year(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.year:0>4}"
        return ""

    def month(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.month:0>2}"
        return ""

    def day(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.day:0>2}"
        return ""

    def hour(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.hour:0>2}"
        return ""

    def minute(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.minute:0>2}"
        return ""

    def second(self) -> str:
        dt: Optional[datetime.datetime] = self._date_time()
        if dt is not None:
            return f"{dt.second:0>2}"
        return ""

    def original(self) -> str:
        filename: Optional[str] = self._filename()
        if filename is not None:
            return filename
        return ""

    def camera_maker(self) -> str:
        if self._has_file():
            exif_value: Optional[str] = self._file.camera_maker().value()
            if exif_value is not None:
                return self._fix_string(exif_value)
        return ""

    def camera_model(self) -> str:
        if self._has_file():
            exif_value: Optional[str] = self._file.camera_model().value()
            if exif_value is not None:
                return self._fix_string(exif_value)
        return ""

    def text_upto(self, text: str, is_include: bool) -> str:
        filename: Optional[str] = self._filename()
        if filename is not None:
            pos: int = filename.find(text)
            if is_include:
                pos += len(text)
            return filename[:pos]
        return ""

    def text_from(self, text: str, is_include: bool) -> str:
        filename: Optional[str] = self._filename()
        if filename is not None:
            pos: int = filename.find(text)
            if not is_include:
                pos += len(text)
            return filename[pos:]
        return ""
