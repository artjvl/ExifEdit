from typing import Optional
import datetime
import re

from package.ExifFile import ExifFile
from package.ChangeDateTaken import ChangeDateTaken


class ExifMap(object):
    _file: Optional[ExifFile]
    _dt: Optional[datetime.datetime]

    def __init__(self, change_date_taken: ChangeDateTaken) -> None:
        self._file = None
        self._change_date_taken = change_date_taken

    # private
    def _fix_string(self, text: str, replacement: str = "-") -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", replacement, text)

    def _has_date_time(self) -> bool:
        return self._date_time is not None

    def _date_time(self, file: ExifFile) -> Optional[datetime.datetime]:
        dt: Optional[datetime.datetime] = file.date_taken().value()
        return self._change_date_taken.convert_date_taken(dt)

    # public
    def filename(self, file: ExifFile) -> Optional[str]:
        return file.filename().value()

    def basename(self, file: ExifFile) -> Optional[str]:
        filename_: Optional[str] = self.filename(file)
        if filename_ is not None:
            return filename_.split(".")[:-1]
        return None

    def extension(self, file: ExifFile) -> Optional[str]:
        filename_: Optional[str] = self.filename(file)
        if filename_ is not None:
            return filename_.split(".")[-1]
        return None

    def year(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.year:0>4}"
        return None

    def month(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.month:0>2}"
        return None

    def day(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.day:0>2}"
        return None

    def hour(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.hour:0>2}"
        return None

    def minute(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.minute:0>2}"
        return None

    def second(self, file: ExifFile) -> Optional[str]:
        dt: Optional[datetime.datetime] = self._date_time(file)
        if dt is not None:
            return f"{dt.second:0>2}"
        return None

    def camera_maker(self, file: ExifFile) -> Optional[str]:
        exif_value: Optional[str] = file.camera_maker().value()
        if exif_value is not None:
            return self._fix_string(exif_value)
        return None

    def camera_model(self, file: ExifFile) -> Optional[str]:
        exif_value: Optional[str] = file.camera_model().value()
        if exif_value is not None:
            return self._fix_string(exif_value)
        return None

    def text_upto(self, file: ExifFile, text: str, is_include: bool) -> Optional[str]:
        filename: Optional[str] = self._filename(file)
        if filename is not None:
            pos: int = filename.find(text)
            if is_include:
                pos += len(text)
            return filename[:pos]
        return None

    def text_from(self, file: ExifFile, text: str, is_include: bool) -> Optional[str]:
        filename: Optional[str] = self._filename(file)
        if filename is not None:
            pos: int = filename.find(text)
            if not is_include:
                pos += len(text)
            return filename[pos:]
        return None
