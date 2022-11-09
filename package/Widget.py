from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from typing import Optional


class Widget(QWidget):
    # def __init__(self, parent: Optional[QWidget] = ..., f: Qt.WindowType = ...) -> None:
    #     super().__init__(parent, f)
    #     print('widget')

    def __init__(self) -> None:
        super().__init__()
        print("widget")
