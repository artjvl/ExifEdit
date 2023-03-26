from __future__ import annotations
from typing import Optional, List

from PySide6 import QtCore, QtWidgets


class NestedListItem(QtWidgets.QWidget):

    # attributes
    _is_exclusive: bool
    _widget_layout: QtWidgets.QLayout
    _widget_container: QtWidgets.QWidget
    _children: List[NestedListItem]
    _text: str
    _checkbox: Optional[QtWidgets.QCheckBox]
    _widget: Optional[QtWidgets.QWidget]

    # signals
    _signal_checked = QtCore.Signal(bool)
    signal_checked = QtCore.Signal(bool)

    def __init__(
        self,
        text: Optional[str] = None,
        widget: Optional[QtWidgets.QWidget] = None,
        is_exclusive: bool = False,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._children = []
        self._widget = widget
        self._is_exclusive = is_exclusive

        # layout
        layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # checkbox
        self._text = ""
        self._checkbox = None
        left_margin: int = 0
        if text is not None:
            self._text = text
            self._checkbox = QtWidgets.QCheckBox(text)
            self._checkbox.stateChanged.connect(self.on_state_changed)
            layout.addWidget(self._checkbox)
            left_margin = 20

        # widget-container
        self._widget_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self._widget_layout.setContentsMargins(left_margin, 0, 0, 0)
        self._widget_container: QtWidgets.QWidget = QtWidgets.QWidget()
        self._widget_container.setLayout(self._widget_layout)
        layout.addWidget(self._widget_container)

        # widgets
        if widget is not None:
            self._widget_layout.addWidget(widget)

        if parent is not None:
            self.parent.enabledChanged.connect(self.on_enabled)

        self._update(is_emit=False)

    # protected
    def _set_checked(self, is_checked: bool, is_emit: bool) -> None:
        if self._checkbox is not None:

            # checkbox
            self._checkbox.blockSignals(True)
            self._checkbox.setChecked(is_checked)
            self._checkbox.blockSignals(False)

            # update
            self._update(is_emit=is_emit)

    def _update(self, is_emit: bool) -> None:
        is_checked: bool = self.is_checked()

        # enable
        # self._widget_container.setEnabled(is_checked)
        if self.has_widget():
            self._widget.setEnabled(is_checked)
        for child in self._children:
            child.setEnabled(is_checked)

        # signals
        self.signal_checked.emit(is_checked)
        if is_emit:
            self._signal_checked.emit(is_checked)

    # public
    def text(self) -> str:
        return self._text

    def has_widget(self) -> bool:
        return self._widget is not None

    def widget(self) -> Optional[QtWidgets.QWidget]:
        return self._widget

    def add_child(
        self,
        text: str,
        widget: Optional[QtWidgets.QWidget] = None,
        is_exclusive: bool = False,
    ) -> NestedListItem:
        index: int = len(self._children)
        new = self.__class__(text, widget=widget, is_exclusive=is_exclusive)
        new.setEnabled(self.is_checked())
        new._signal_checked.connect(
            lambda is_checked: self.on_child_check(index, is_checked)
        )
        self._children.append(new)
        self._widget_layout.addWidget(new)

        if self._is_exclusive and index == 0:
            new.set_checked(True)

        return new

    def is_checked(self) -> bool:
        if self._checkbox is not None:
            return self._checkbox.isChecked()
        return True

    def set_checked(self, is_checked: bool) -> None:
        if is_checked != self.is_checked():
            self._set_checked(is_checked, is_emit=True)

    # override
    def setEnabled(self, is_enabled: bool) -> None:
        super().setEnabled(is_enabled)

        if self.has_widget():
            self._widget.setEnabled(self.is_checked())
        for child in self._children:
            child.setEnabled(is_enabled)

        if is_enabled and self.is_checked():
            self.signal_checked.emit(True)

    # handlers
    def on_state_changed(self, state: int) -> None:
        is_checked: bool = state == 2
        assert is_checked == self.is_checked()
        self._update(is_emit=True)

    def on_child_check(self, index: int, is_checked: bool):
        # Handler for signal '_signal_checked', which is emitted from a child NestedListItem when
        # its checkbox has been checked from the outside, i.e.:
        # - via UI check (with signal 'stateChanged'), or
        # - via method call 'set_checked()'

        if self._is_exclusive:
            child: NestedListItem
            if is_checked:
                # uncheck all siblings
                for i, child in enumerate(self._children):
                    if i != index:
                        child._set_checked(False, is_emit=False)
            else:
                # check first other child
                new_index: int = 0
                if new_index == index:
                    new_index = 1

                child = self._children[new_index]
                child._set_checked(True, is_emit=False)
