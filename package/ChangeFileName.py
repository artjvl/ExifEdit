from __future__ import annotations
import re
import functools
from typing import Optional, List, Dict, Callable

from PySide6 import QtCore, QtWidgets

from package.Image import Image
from package.ExifMap import ExifMap
from package.NestedList import NestedListItem
from package.ChangeDateTaken import ChangeDateTaken


class ChangeFileName(QtWidgets.QWidget):

    _SETTING: str = "filename"
    _nested: NestedListItem
    _settings: QtCore.QSettings
    _img: Optional[Image]
    _text: Optional[str]

    _map: ExifMap
    _tags: Dict[str, Callable]

    signal_changed = QtCore.Signal(str)

    def __init__(
        self,
        change_date_taken: ChangeDateTaken,
        settings: QtCore.QSettings,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._text = ""
        if self._settings.contains(self._SETTING):
            text: Optional[str] = self._settings.value(self._SETTING)
            if text is not None:
                self._text = text

        self._img = None
        change_date_taken.signal_changed.connect(self.emit_filename)

        self._map = ExifMap(change_date_taken)
        self._tags = {
            "ORG": Tag("Original file name", self._map.basename),
            "YYYY": Tag("Year", self._map.year),
            "MM": Tag("Month", self._map.month),
            "DD": Tag("Day", self._map.day),
            "hh": Tag("Hour", self._map.hour),
            "mm": Tag("Minute", self._map.minute),
            "ss": Tag("Second", self._map.second),
            "MAK": Tag("Camera maker", self._map.camera_maker),
            "MOD": Tag("Camera model", self._map.camera_model),
            "UPT:": Tag(
                "Up to", lambda img, text: self._map.text_upto(img, text, False)
            ),
            "UPTI:": Tag(
                "Up to and including",
                lambda img, text: self._map.text_upto(img, text, True),
            ),
            "FRM:": Tag(
                "From", lambda img, text: self._map.text_from(img, text, False)
            ),
            "FRMI:": Tag(
                "From and including",
                lambda img, text: self._map.text_from(img, text, True),
            ),
        }

        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        tags: Dict[str, str] = {}
        for tag, element in self._tags.items():
            tags[tag] = element.description()

        widget: FileNameFormat = FileNameFormat(self._text, tags)
        widget.signal_text_changed.connect(self.on_text_changed)
        layout.addWidget(widget)

        self._nested = NestedListItem(text="Change File name", widget=widget)
        self._nested.signal_checked.connect(self.emit_filename)

        # self._nested.signal_checked.connect(self.on_update)
        layout.addWidget(self._nested)

    def is_checked(self) -> bool:
        return self._nested.is_checked()

    def set_file(self, img: Optional[Image]) -> None:
        self._img = img
        self.emit_filename()

    def has_file(self) -> bool:
        return self._img is not None

    def replace_tags(self, text: str, tags: Dict[str, str]) -> str:
        for tag, new in tags.items():
            assert tag in text
            full_tag: str = f"[{tag}]"
            if new is None:
                new = ""
            text = text.replace(full_tag, new)
        return text

    def compile_filename(self, img: Image, text: str) -> Optional[str]:
        if len(text) > 0:
            tag_pattern = r"\[([^\[\]]*)\]"
            tags: List[str] = re.findall(tag_pattern, text)

            mapping: Dict[str, str] = {}
            for tag in tags:
                split: List[str] = tag.rsplit(":", 1)
                element: str
                if len(split) > 1:
                    # tags with arguments
                    subtag = f"{split[0]}:"
                    arg: str = split[1]
                    element = self._tags[subtag].mapping(img, arg)
                else:
                    # tags without arguments
                    element = self._tags[tag].mapping(img)
                mapping[tag] = element

            elements: List[str] = list(mapping.values())
            if len(elements) > 0 and any(element is not None for element in elements):
                new_filename: str = self.replace_tags(text, mapping)
                if any(char.isalnum() for char in new_filename):
                    return f"{new_filename}{img.extension()}"
        return None

    def convert_filename(self, img: Optional[Image]) -> Optional[str]:
        if self.is_checked() and self.has_file():
            new_filename: Optional[str] = self.compile_filename(img, self._text)
            if new_filename is not None:
                return new_filename
        return None

    # emit
    def emit_filename(self) -> Optional[str]:
        filename: Optional[str] = self.convert_filename(self._img)
        if filename is None and self.has_file():
            filename = self._img.filename()
        self.signal_changed.emit(filename)

    # handlers
    def on_text_changed(self, text: str, tags: List[str]) -> None:
        self._text = text
        self._settings.setValue("filename", text)
        self.emit_filename()


class FileNameFormat(QtWidgets.QWidget):
    _tags: List[str]

    signal_text_changed = QtCore.Signal(str, list)

    def __init__(
        self,
        text: str,
        tags: Dict[str, str],
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._tags = list(tags.keys())

        # layout
        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        # line-edit
        self._line_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(text)
        layout.addWidget(self._line_edit)
        self._line_edit.textChanged.connect(self.on_text_changed)

        # menu
        menu = QtWidgets.QMenu()
        menu.setStyleSheet(
            "QMenu::item {padding: 2px 5px 2px 2px;}"
            "QMenu::item:selected {background-color: rgb(0, 85, 127); color: rgb(255, 255, 255);}"
        )
        for tag, description in tags.items():
            menu_text: str = f"[{tag}]\t{description}"
            action: QtWidgets.QAction = menu.addAction(menu_text)
            action.triggered.connect(functools.partial(self.add_tag, tag))

        # button
        self._button = QtWidgets.QPushButton("Add element")
        self._button.setStyleSheet("text-align:left")
        self._button.setMenu(menu)
        self._button.menu()  # required to associate QMenu to QPushButton (PySide6 bug?)

        # Create a layout and add the button to it
        layout.addWidget(self._button)

    def add_tag(self, tag: str) -> None:
        pos: int = self._line_edit.cursorPosition()
        text: str = self._line_edit.text()
        right_text: str = text[pos:]

        index_left: int = 1024
        if "[" in right_text:
            index_left = right_text.find("[")
        index_right: int = 1024
        if "]" in right_text:
            index_right = right_text.find("]")
        if index_right < index_left:
            self._line_edit.setCursorPosition(pos + index_right + 1)

        self._line_edit.insert(f"[{tag}]")

    # handler
    def on_text_changed(self, text: str):
        pattern = (
            r"^(?:\[[^[\]]*\]|[a-zA-Z0-9_\-\.])*\Z"  # r"^(\[[^\[\]]*\]|[a-zA-Z0-9])*"
        )
        match = re.fullmatch(pattern, text)
        is_match = match is not None
        tag_pattern = r"\[([^\[\]]*)\]"
        tags: List[str] = re.findall(tag_pattern, text)
        tags = [tag.strip() for tag in tags]
        for i, tag in enumerate(tags):
            if ":" in tag:
                tags[i] = f"{tag.split(':')[0]}:"
        is_tag_match: bool = set(tags).issubset(set(self._tags))

        is_valid: bool = is_match and is_tag_match

        if is_valid:
            self._line_edit.setStyleSheet("border: 2px solid white")
            self.signal_text_changed.emit(text, tags)
        else:
            self._line_edit.setStyleSheet("border: 2px solid red")
        self._button.setEnabled(is_valid)


class Tag(object):
    _description: str
    _mapping: Callable[[], str]

    def __init__(self, description: str, mapping: Callable[[], str]) -> None:
        self._description = description
        self._mapping = mapping

    def description(self) -> str:
        return self._description

    def mapping(self, *args) -> Callable[[], str]:
        return self._mapping(*args)
